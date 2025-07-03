#pragma once

#include <string>
#include <curl/curl.h>

class NetworkClient {
public:
    NetworkClient();
    ~NetworkClient();
    
    void initialize();
    std::string get(const std::string& url);
    
private:
    CURL* curl_handle_;
};