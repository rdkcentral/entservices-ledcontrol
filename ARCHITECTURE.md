# LEDControl Service - System Architecture

## Overview

The LEDControl service is a **Thunder plugin** for RDK (Reference Design Kit) that provides programmatic control over LED indicators on set-top boxes, streaming devices, and other customer premise equipment. It implements a standardized interface for managing LED states to indicate device operational status, connectivity states, and system events.

## Architectural Components

### 1. Plugin Architecture (Thunder)

The system follows Thunder's plugin architecture pattern:

```
┌─────────────────────────────────────────┐
│           Thunder Core             │
├─────────────────────────────────────────┤
│         LEDControl Plugin               │
├─────────────────────────────────────────┤
│      LEDControlImplementation           │
├─────────────────────────────────────────┤
│         DS-HAL (Device Settings)        │
├─────────────────────────────────────────┤
│        Hardware LED Controller          │
└─────────────────────────────────────────┘
```

#### Core Components:

- **LEDControl Plugin** (`LEDControl.cpp/.h`): Main plugin entry point, implements `PluginHost::IPlugin` interface
- **LEDControlImplementation** (`LEDControlImplementation.cpp/.h`): Business logic implementation, implements `Exchange::ILEDControl` interface
- **Module** (`Module.cpp/.h`): Plugin module registration and metadata

### 2. Interface Layer

#### JSON-RPC API
- Exposes REST endpoints through Thunder's JSON-RPC mechanism
- Automatic marshalling/unmarshalling between C++ objects and JSON
- Registered via `Exchange::JLEDControl::Register()`

#### C++ COM Interface
- Direct C++ interface (`Exchange::ILEDControl`)
- Type-safe method calls for embedded applications
- Thread-safe operation with critical section locking

### 3. Hardware Abstraction

#### DS-HAL Integration
The service integrates with RDK's Device Settings Hardware Abstraction Layer (DS-HAL):

- **dsFPD (Device Settings Front Panel Display)** APIs
- Platform-specific LED controller drivers
- Error code mapping from DS errors to Thunder error codes
- State validation against hardware capabilities

#### Platform Initialization
- Lazy initialization with `dsFPInit()`
- Background worker thread for capability discovery
- Graceful cleanup with `dsFPTerm()`
- Exception handling for hardware failures

### 4. Threading and Concurrency

#### Thread Safety
- **Critical Section Locking**: All hardware operations protected by `Core::CriticalSection`
- **Worker Pool Integration**: Background tasks use Thunder's worker pool
- **Asynchronous Initialization**: LED capability discovery runs asynchronously

#### Connection Management
- Out-of-process communication support
- Connection lifecycle management
- Graceful termination with process cleanup

### 5. State Management

#### LED State Mapping
Bidirectional state mapping between abstract and hardware representations:

```cpp
LEDControlState → dsFPDLedState_t → Hardware Register
```

#### Supported States:
- **NONE**: LED disabled
- **ACTIVE**: Device operational  
- **STANDBY**: Low-power mode
- **WPS_CONNECTING**: WiFi Protected Setup in progress
- **WPS_CONNECTED**: WPS successfully connected
- **WPS_ERROR**: WPS connection failed
- **FACTORY_RESET**: Factory reset in progress
- **USB_UPGRADE**: Firmware upgrade via USB
- **DOWNLOAD_ERROR**: Software download failure

#### Dynamic Capability Discovery
- Runtime detection of hardware-supported LED states
- Bitfield-based capability caching
- Validation of requests against hardware capabilities

### 6. Error Handling and Resilience

#### Layered Error Handling
1. **Hardware Errors**: DS-HAL error codes mapped to standard errors
2. **Validation Errors**: Parameter and state validation
3. **System Errors**: Platform initialization and resource failures
4. **Exception Safety**: Comprehensive exception catching and logging

#### Logging Integration
- Structured logging via Thunder's logging system
- Debug, info, warning, and error level categorization
- Performance and debugging trace support

### 7. Configuration and Deployment

#### Plugin Configuration
- **Autostart**: Configurable automatic plugin activation
- **Startup Order**: Dependency-based initialization sequence
- **Platform Preconditions**: Ensures hardware availability
- **Service Callsign**: `org.rdk.LEDControl` for service identification

#### Build System Integration
- CMake-based build system with Thunder integration
- Separate plugin and implementation libraries
- Automated dependency resolution
- Platform-specific configuration support

### 8. Testing Architecture

#### L2 Testing Framework
- Comprehensive test suite using Google Test framework
- Hardware abstraction layer mocking for unit tests
- Both JSON-RPC and C++ interface testing
- Edge case and error condition validation

#### Mock Integration
- DS-HAL function mocking for isolated testing
- Deterministic test scenarios
- Coverage for all LED states and error conditions

## Scalability and Extensibility

### Plugin Isolation
- Out-of-process execution capability
- Memory and resource isolation
- Independent lifecycle management
- Crash recovery mechanisms

### Interface Versioning
- Version-controlled COM interfaces
- Backward compatibility support
- API evolution without breaking changes

### Platform Portability
- Hardware abstraction through DS-HAL
- Platform-specific build configurations
- Configurable LED state support per device type

## Security Considerations

### Resource Protection
- Exclusive LED hardware access control
- Validated state transitions
- Protected against invalid state requests

### Process Isolation
- Sandboxed plugin execution
- Controlled inter-process communication
- Memory boundary protection

This architecture enables reliable, scalable LED control across diverse RDK hardware platforms while maintaining clean separation of concerns and robust error handling.