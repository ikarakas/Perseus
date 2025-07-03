#include <iostream>
#include <string>
#include <vector>
#include <memory>

// Boost libraries
#include <boost/filesystem.hpp>
#include <boost/system/error_code.hpp>
#include <boost/thread.hpp>

// OpenSSL
#include <openssl/ssl.h>
#include <openssl/crypto.h>

// CURL
#include <curl/curl.h>

// fmt library
#include <fmt/format.h>

// SQLite
#include <sqlite3.h>

// zlib
#include <zlib.h>

#include "network_client.h"
#include "data_processor.h"

int main() {
    std::cout << fmt::format("SBOM Test Application v{}.{}.{}\n", 1, 0, 0);
    
    // Initialize CURL
    curl_global_init(CURL_GLOBAL_DEFAULT);
    
    // Initialize OpenSSL
    SSL_load_error_strings();
    SSL_library_init();
    
    // Use Boost filesystem
    boost::filesystem::path current_path = boost::filesystem::current_path();
    std::cout << "Current directory: " << current_path.string() << std::endl;
    
    // Create network client
    auto client = std::make_unique<NetworkClient>();
    client->initialize();
    
    // Create data processor
    DataProcessor processor;
    processor.process_data("sample data");
    
    // Cleanup
    curl_global_cleanup();
    
    return 0;
}