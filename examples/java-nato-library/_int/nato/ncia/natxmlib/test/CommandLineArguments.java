/*
 * To change this license header, choose License Headers in Project Properties.
 * To change this template file, choose Tools | Templates
 * and open the template in the editor.
 */
package _int.nato.ncia.natxmlib.test;

import java.util.Collections;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.TreeMap;
import java.util.logging.Level;
import java.util.logging.LogManager;
import java.util.logging.Logger;

/**
 *
 * @author mike
 */
public class CommandLineArguments {
    protected Map<String, List<String>> optionMap = new TreeMap<>();
    protected LinkedList<String> argList = new LinkedList<>();
    
    protected void parse(String key, String value) {
        List<String> list = optionMap.get(key);
        if(list==null) {
            list = new LinkedList<>();
            optionMap.put(key, list);
        }
        list.add(value);        
    }
    protected void parse(String arg) {
        if(arg.startsWith("--")) {
            if(arg.contains("=")) {
                String key=arg.substring(2,arg.indexOf("=")).toLowerCase();
                String value=arg.substring(arg.indexOf("=")+1);
                parse(key,value);
            }else {
                String key=arg.substring(2).toLowerCase();
                parse(key,"");
            }
        }else {
            argList.add(arg);
        }
        
    }
    public void parse(String[] args) {
        for(String s : args) {
            parse(s);
        }
    }
    public boolean contains(String key) {
        return optionMap.containsKey(key);
    }
    public boolean contains(String key, String value) {
        List<String> list = optionMap.get(key);
        if(list==null) {
            return false;
        }
        for(String s : list) {
            if(s.compareTo(value)==0) {
                return true;
            }
        }
        return false;
    }
    public Set<String> keys() {
        return optionMap.keySet();
    }
    public String asStringValue(String key) {
        List<String> list = optionMap.get(key);
        if(list==null) {
            return null;
        }
        if(list.isEmpty()) {
            return null;
        }
        return list.iterator().next();
    }
    public List<String> getArguments() {
        return argList;
    }
    public String getOptionValue(String key, String def) {
        List<String> list = optionMap.get(key);
        if(list==null) {
            return def;
        }
        if(list.isEmpty()) {
            return def;
        }
        return list.iterator().next();        
    }
    public List<String> getOptions(String key) {
        List<String> list = optionMap.get(key);
        if(list==null) {
            return Collections.EMPTY_LIST;
        }
        return list;
    }
    public void setLogLevel(String name, Level def) {
        Logger l = LogManager.getLogManager().getLogger(name);
        if(l!=null) {
            l.setLevel(getLogLevel(def));
        }
    }
    public Level getLogLevel(Level def) {
        String str = getOptionValue("loglevel", null);
        if(str==null) {
            return def;
        }
        switch(str.toUpperCase()) {
            case "ERROR":
            case "SEVERE":
                return Level.SEVERE;
            case "WARN":
            case "WARNING":
                return Level.WARNING;
            case "INFO":
                return Level.INFO;
            case "TRACE":
                return Level.FINER;
            case "DEBUG":
                return Level.FINEST;
            default:
                return def;
        }
    }
}
