/**
* If not stated otherwise in this file or this component's LICENSE
* file the following copyright and licenses apply:
*
* Copyright 2025 RDK Management
*
* Licensed under the Apache License, Version 2.0 (the "License");
* you may not use this file except in compliance with the License.
* You may obtain a copy of the License at
*
* http://www.apache.org/licenses/LICENSE-2.0
*
* Unless required by applicable law or agreed to in writing, software
* distributed under the License is distributed on an "AS IS" BASIS,
* WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
* See the License for the specific language governing permissions and
* limitations under the License.
**/

#include "LEDControlImplementation.h"

#include <core/Portability.h>
#include <interfaces/ILEDControl.h>

#include <binder/IServiceManager.h>
#include <binder/ProcessState.h>
#include <utils/StrongPointer.h>
#include <com/rdk/hal/indicator/IIndicatorManager.h>
#include <com/rdk/hal/indicator/IIndicator.h>
#include <com/rdk/hal/indicator/Capabilities.h>

#include "UtilsLogging.h"

namespace WPEFramework
{
    namespace Plugin
    {
        SERVICE_REGISTRATION(LEDControlImplementation, 1, 0);

        LEDControlImplementation::LEDControlImplementation()
        : m_isPlatInitialized(false)
        , m_indicatorManager(nullptr)
        , m_indicator(nullptr)
        {
            LOGINFO("LEDControlImplementation Constructor called\n");
            LOGINFO("Acquiring AIDL indicator service\n");
            try {
                android::ProcessState::self()->startThreadPool();

                android::sp<android::IBinder> binderSvc =
                    android::defaultServiceManager()->getService(
                        android::String16(com::rdk::hal::indicator::IIndicatorManager::serviceName().c_str()));
                if (binderSvc == nullptr) {
                    LOGERR("Failed to get indicator service from Binder ServiceManager\n");
                    return;
                }

                m_indicatorManager = android::interface_cast<com::rdk::hal::indicator::IIndicatorManager>(binderSvc);
                if (m_indicatorManager == nullptr) {
                    LOGERR("Failed to cast Binder to IIndicatorManager\n");
                    return;
                }

                std::vector<com::rdk::hal::indicator::IIndicator::Id> indicatorIds;
                android::binder::Status st = m_indicatorManager->getIndicatorIds(&indicatorIds);
                if (!st.isOk() || indicatorIds.empty()) {
                    LOGERR("getIndicatorIds failed or returned empty list\n");
                    m_indicatorManager.clear();
                    return;
                }

                st = m_indicatorManager->getIndicator(indicatorIds[0], &m_indicator);
                if (!st.isOk() || m_indicator == nullptr) {
                    LOGERR("getIndicator failed\n");
                    m_indicatorManager.clear();
                    return;
                }

                LOGINFO("AIDL indicator service acquired successfully\n");
                m_isPlatInitialized = true;
            } catch (...) {
                LOGERR("Exception caught during AIDL indicator init\n");
            }
        }

        LEDControlImplementation::~LEDControlImplementation()
        {
            LOGINFO("LEDControlImplementation Destructor called\n");
            if (m_isPlatInitialized) {
                LOGINFO("Releasing AIDL indicator handles\n");
                m_indicator.clear();
                m_indicatorManager.clear();
                m_isPlatInitialized = false;
            }
        }

        /************************ Helper Functions *************************/
        namespace {
            using LEDControlState = WPEFramework::Exchange::ILEDControl::LEDControlState;

            struct LEDStateMapEntry {
                LEDControlState ledState;
                const char* name;
                const char* aidlName;
            };

            struct AidlAliasEntry {
                const char* aidlName;
                LEDControlState ledState;
            };

            constexpr LEDStateMapEntry kLEDStateMap[] = {
                { LEDControlState::LEDSTATE_NONE,           "NONE",           nullptr },
                { LEDControlState::LEDSTATE_ACTIVE,         "ACTIVE",         "ACTIVE" },
                { LEDControlState::LEDSTATE_STANDBY,        "STANDBY",        "STANDBY" },
                { LEDControlState::LEDSTATE_WPS_CONNECTING, "WPS_CONNECTING", "WPS_CONNECTING" },
                { LEDControlState::LEDSTATE_WPS_CONNECTED,  "WPS_CONNECTED",  "WPS_CONNECTED" },
                { LEDControlState::LEDSTATE_WPS_ERROR,      "WPS_ERROR",      "WPS_ERROR" },
                { LEDControlState::LEDSTATE_FACTORY_RESET,  "FACTORY_RESET",  "FULL_SYSTEM_RESET" },
                { LEDControlState::LEDSTATE_USB_UPGRADE,    "USB_UPGRADE",    "USB_UPGRADE" },
                { LEDControlState::LEDSTATE_DOWNLOAD_ERROR, "DOWNLOAD_ERROR", "SOFTWARE_DOWNLOAD_ERROR" },
            };

            constexpr AidlAliasEntry kAidlAliasMap[] = {
                { "IP_ACQUIRED", LEDControlState::LEDSTATE_ACTIVE },
                { "OFF",         LEDControlState::LEDSTATE_STANDBY },
                { "DEEP_SLEEP",  LEDControlState::LEDSTATE_STANDBY },
            };

            const LEDStateMapEntry* findByLEDState(const LEDControlState state)
            {
                for (const auto& entry : kLEDStateMap) {
                    if (entry.ledState == state) {
                        return &entry;
                    }
                }
                return nullptr;
            }

            bool findByAidlState(const android::String16& aidlState, LEDControlState& state)
            {
                for (const auto& entry : kLEDStateMap) {
                    if (entry.aidlName != nullptr && aidlState == android::String16(entry.aidlName)) {
                        state = entry.ledState;
                        return true;
                    }
                }

                for (const auto& alias : kAidlAliasMap) {
                    if (aidlState == android::String16(alias.aidlName)) {
                        state = alias.ledState;
                        return true;
                    }
                }

                return false;
            }
        }

        /***
         * @brief: Map ILEDControl::LEDControlState to AIDL indicator state string
         * @param[in] state The LED control state
         * @return Corresponding AIDL state string, or nullptr if not mappable
         */
        static const char* ledControlStateToAidlState(WPEFramework::Exchange::ILEDControl::LEDControlState state)
        {
            const auto* entry = findByLEDState(state);
            return (entry != nullptr) ? entry->aidlName : nullptr;
        }

        /***
         * @brief: Map AIDL indicator state string to ILEDControl::LEDControlState
         * @param[in] aidlState The AIDL state string
         * @param[out] state The corresponding LEDControlState
         * @return true on success, false if the string is not recognised
         */
        static bool aidlStateToLEDControlState(const android::String16& aidlState,
                                               WPEFramework::Exchange::ILEDControl::LEDControlState& state)
        {
            return findByAidlState(aidlState, state);
        }

        /***
         * @brief: Map LEDControlState to display string (for response building)
         * @param[in] state The LEDControlState
         * @return Corresponding string representation if valid, otherwise nullptr
         */
        static const char* LEDControlStateToString(WPEFramework::Exchange::ILEDControl::LEDControlState state)
        {
            const auto* entry = findByLEDState(state);
            return (entry != nullptr) ? entry->name : nullptr;
        }

        /************************ Plugin Methods ************************/

        Core::hresult LEDControlImplementation::GetSupportedLEDStates(IStringIterator*& supportedLEDStates, bool& success)
        {
            LOGINFO("");
            if (!m_isPlatInitialized || m_indicator == nullptr) {
                LOGERR("AIDL indicator not available\n");
                return Core::ERROR_NOT_SUPPORTED;
            }

            com::rdk::hal::indicator::Capabilities caps;
            {
                Core::SafeSyncType<Core::CriticalSection> lock(_adminLock);
                android::binder::Status st = m_indicator->getCapabilities(&caps);
                if (!st.isOk()) {
                    LOGERR("IIndicator::getCapabilities failed\n");
                    return Core::ERROR_GENERAL;
                }
            }

            std::list<std::string> stateNames;
            for (const auto& aidlState : caps.supportedStates) {
                WPEFramework::Exchange::ILEDControl::LEDControlState state;
                if (aidlStateToLEDControlState(aidlState, state)) {
                    const char* str = LEDControlStateToString(state);
                    if (str != nullptr) {
                        stateNames.emplace_back(str);
                    }
                } else {
                    LOGWARN("AIDL returned unrecognised state, skipping\n");
                }
            }
            supportedLEDStates = Core::Service<RPC::StringIterator>::Create<RPC::IStringIterator>(stateNames);
            success = true;
            return Core::ERROR_NONE;
        }

        Core::hresult LEDControlImplementation::GetLEDState(WPEFramework::Exchange::ILEDControl::LEDControlState& ledState)
        {
            LOGINFO("");
            if (!m_isPlatInitialized || m_indicator == nullptr) {
                LOGERR("AIDL indicator not available\n");
                return Core::ERROR_NOT_SUPPORTED;
            }

            android::String16 aidlState;
            {
                Core::SafeSyncType<Core::CriticalSection> lock(_adminLock);
                android::binder::Status st = m_indicator->get(&aidlState);
                if (!st.isOk()) {
                    LOGERR("IIndicator::get failed\n");
                    return Core::ERROR_GENERAL;
                }
            }

            if (!aidlStateToLEDControlState(aidlState, ledState)) {
                LOGWARN("Unrecognised AIDL state returned by IIndicator::get; defaulting to LEDSTATE_NONE\n");
                ledState = WPEFramework::Exchange::ILEDControl::LEDSTATE_NONE;
                return Core::ERROR_NONE;
            }
            return Core::ERROR_NONE;
        }

        // New overload of GetLEDState to maintain backward compatibility
        Core::hresult LEDControlImplementation::GetLEDState(WPEFramework::Exchange::ILEDControl::LEDState& ledState)
        {
            LOGINFO("");
            WPEFramework::Exchange::ILEDControl::LEDControlState state = WPEFramework::Exchange::ILEDControl::LEDSTATE_MAX;
            Core::hresult hr = GetLEDState(state);
            if (hr == Core::ERROR_NONE) {
                ledState.state = state;
            }
            return hr;
        }

        Core::hresult LEDControlImplementation::SetLEDState(const WPEFramework::Exchange::ILEDControl::LEDControlState& state, bool& success)
        {
            LOGINFO("");
            if (!m_isPlatInitialized || m_indicator == nullptr) {
                LOGERR("AIDL indicator not available\n");
                return Core::ERROR_NOT_SUPPORTED;
            }

            const char* aidlStateStr = ledControlStateToAidlState(state);
            if (aidlStateStr == nullptr) {
                LOGERR("Invalid LEDControlState %d cannot be mapped to AIDL state\n", static_cast<int>(state));
                return Core::ERROR_BAD_REQUEST;
            }

            bool setResult = false;
            {
                Core::SafeSyncType<Core::CriticalSection> lock(_adminLock);
                android::binder::Status st = m_indicator->set(android::String16(aidlStateStr), &setResult);
                if (!st.isOk() || !setResult) {
                    LOGERR("IIndicator::set(%s) failed\n", aidlStateStr);
                    return Core::ERROR_GENERAL;
                }
            }
            success = true;
            return Core::ERROR_NONE;
        }
    } // namespace Plugin
} // namespace WPEFramework
