/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

/**
 *
 * @author mike
 */
public class Config {
    protected static Config INSTANCE  = new Config();
    
    protected boolean ignoreUTC=false;
    
    protected boolean useGINSReplay=false;
    protected String ginsReplayFileName="";
    
    protected boolean runCardmon=false;
    
    protected String serialPortName="COM5";
    protected int serialBaudRate=2500000;
    protected boolean serialFlowControl=true;
    
    protected String midsIP="147.21.1.207";
    protected int midsPort=1024;
    
    protected String recordingPath="../recordings";
    protected boolean recordingEnabled=true;
    
    protected boolean jicDumpEnabled=true;
    
    protected boolean midsNavUseUTC=true;
    
    protected boolean rarpdRun=true;
    
    private Config() {
        
    }

    public boolean isMidsNavUseUTC() {
        return midsNavUseUTC;
    }

    public boolean isIgnoreUTC() {
        return ignoreUTC;
    }

    public boolean isUseGINSReplay() {
        return useGINSReplay;
    }

    public String getGinsReplayFileName() {
        return ginsReplayFileName;
    }

    public boolean isRunCardmon() {
        return runCardmon;
    }

    public String getJICPortName() {
        return serialPortName;
    }

    public int getJICBaudRate() {
        return serialBaudRate;
    }

    public boolean isJICFlowControl() {
        return serialFlowControl;
    }

    public String getMidsIP() {
        return midsIP;
    }

    public int getMidsPort() {
        return midsPort;
    }

    public String getRecordingPath() {
        return recordingPath;
    }

    public boolean isRecordingEnabled() {
        return recordingEnabled;
    }

    public boolean isJICDumpEnabled() {
        return jicDumpEnabled;
    }
    
    public static Config getInstance() {
        return INSTANCE;
    }
    protected boolean set(String var, String val) {
        switch(var.toLowerCase()) {
            case "utc.ignore": {
                ignoreUTC=Boolean.parseBoolean(val);
                break;
            }
            case "mids.ip" : {
                midsIP=val;
                break;
            }
            case "mids.port": {
                midsPort=Integer.parseInt(val);
                break;
            }
            case "jic.port": {
                serialPortName=val;
                break;
            }
            case "jic.baud": {
                serialBaudRate=Integer.parseInt(val);
                break;
            }
            case "jic.flow": {
                serialFlowControl=Boolean.parseBoolean(val);
                break;
            }
            case "jic.dump": {
                jicDumpEnabled=Boolean.parseBoolean(val);
                break;
            }
            case "gins.replay": {
                useGINSReplay=Boolean.parseBoolean(val);
                break;
            }
            case "gins.file": {
                ginsReplayFileName=val;
                break;
            }
            case "recording.enabled": {
                recordingEnabled=Boolean.parseBoolean(val);
                break;
            }
            case "recording.path": {
                recordingPath=val;
                break;
            }
            case "cardmon.run": {
                runCardmon=Boolean.parseBoolean(val);
                break;
            }           
            case "mids.nav.useutc" :{
                midsNavUseUTC=Boolean.parseBoolean(val);
                break;
            }
            case "rarpd.run": {
                rarpdRun=Boolean.parseBoolean(val);
                break;
            }
            default:
                return false;                
        }
        return true;
    }

    public void load(String fileName) throws IOException {
        int lineIdx = 1;
        for (String line : Files.lines(Path.of(fileName)).toList()) {
            String[] arr = line.split("=");
            if(line.trim().isEmpty() || (line.startsWith("#"))) {
                lineIdx++;
                continue;
            }
            if (arr.length == 2) {
                try {
                    if(!set(arr[0], arr[1])) {
                        System.err.println("unknown config argument "+arr[0]+" in line:" + lineIdx);                        
                    }
                } catch (Exception ex) {
                    System.err.println("illegal config argument in line:" + lineIdx);
                }
            } else {
                System.err.println("illegal config line:" + lineIdx);
            }
            lineIdx++;
        }
    }
    public void save(String fileName) {
        
    }
}
