cmake_minimum_required(VERSION 3.10)
project(SBOMTestApp VERSION 1.0.0)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Find required packages
find_package(Boost REQUIRED COMPONENTS system filesystem thread)
find_package(OpenSSL REQUIRED)
find_package(CURL REQUIRED)
find_package(fmt REQUIRED)

# Include directories
include_directories(${Boost_INCLUDE_DIRS})
include_directories(${OPENSSL_INCLUDE_DIR})

# Create executable
add_executable(sbom_test_app
    src/main.cpp
    src/network_client.cpp
    src/data_processor.cpp
)

# Link libraries
target_link_libraries(sbom_test_app 
    ${Boost_LIBRARIES}
    OpenSSL::SSL 
    OpenSSL::Crypto
    CURL::libcurl
    fmt::fmt
    pthread
)

# Additional libraries for demonstration
target_link_libraries(sbom_test_app 
    sqlite3
    zlib
)