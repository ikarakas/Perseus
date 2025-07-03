#include "data_processor.h"
#include <iostream>
#include <boost/filesystem.hpp>
#include <fmt/format.h>

DataProcessor::DataProcessor() : db_(nullptr) {
    // Initialize SQLite
    int rc = sqlite3_open(":memory:", &db_);
    if (rc) {
        std::cout << fmt::format("Can't open database: {}\n", sqlite3_errmsg(db_));
    } else {
        std::cout << "SQLite database opened successfully\n";
    }
}

DataProcessor::~DataProcessor() {
    if (db_) {
        sqlite3_close(db_);
    }
}

void DataProcessor::process_data(const std::string& data) {
    std::cout << fmt::format("Processing data: {}\n", data);
    
    // Compress the data
    auto compressed = compress_data(data);
    std::cout << fmt::format("Compressed {} bytes to {} bytes\n", 
                            data.length(), compressed.size());
}

std::vector<uint8_t> DataProcessor::compress_data(const std::string& data) {
    // Simple zlib compression example
    std::vector<uint8_t> compressed;
    uLongf compressed_size = compressBound(data.length());
    compressed.resize(compressed_size);
    
    int result = compress(compressed.data(), &compressed_size,
                         reinterpret_cast<const Bytef*>(data.c_str()), 
                         data.length());
    
    if (result == Z_OK) {
        compressed.resize(compressed_size);
    }
    
    return compressed;
}