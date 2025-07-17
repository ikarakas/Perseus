/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Enum.java to edit this template
 */
package _int.nato.ncia.ginslib;

import tdllib.otg.datafields.Types;

/**
 *
 * @author mike
 */
public enum MessageType {
    T_01("ST", 26),
    T_02("Hybrid Output 1", 29),
    T_03("Calibration", 10),
    //    T_09("Background GPS Output",28),    
    T_04("Hybrid Output 2", 32),
    T_06("FI Output 1", 32),
    T_09("Background GPS Output", 27),
    T_12("GPS Almanach Data", 17),
    T_16("Time Mark Pulse Output 2", 32),
    T_17("GINS/INS Output Data 3", 4),
    T_20("PTTI Output Message", 4),
    T_27("JTIDS Nav Data", 32),
    R_01("Mode CTRL",32),
    R_02("EGI Ref Data",28),
    R_03("Boresight Calibration",10),
    UNKNOWN("Unknown", 0);

    public final static int TA_JTIDS = 2;
    public final static int TA_EGI_1 = 3;
    public final static int TA_EGI_2 = 4;
    public final static int TA_UNDOCUMENTED = 8;
    public final static int TA_IFF_TRANSPONDER = 16;
    public final static int TA_IFF_INTERROGATOR = 17;

    protected String name;
    protected int wordCount;

    MessageType(String name, int wordCount) {
        this.name = name;
        this.wordCount = wordCount;
    }

    public String getName() {
        return name;
    }
    
    public static MessageType identify(int rt, boolean tx, int sa, int wc) {
        if (!tx) {
//            if((sa==27) && (wc==27)) {
//                return T_27;                
//            }
   
            if (rt == TA_JTIDS) {
                switch (sa) {
                    case 2:
                        return T_27;
                    case 3:
                        return T_09;
                    case 4:
                        return T_20;
                    default:
                        return UNKNOWN;
                }
            }
            if ((rt == TA_EGI_1) || (rt == TA_EGI_2)) {
                switch (sa) {
                    case 1:
                        return R_01;
                    case 2:
                        return R_02;
                    case 3:
                        return R_03;
                    case 10:
                        return T_09; 
                }
            }
            if(rt==TA_UNDOCUMENTED) {
                switch(sa) {
                    case 1:
                        return T_01;
                    case 2:
                        return T_02;
                    case 4:
                        return T_04;
                    case 6:
                        return T_06;
                    case 7:
                        return T_02;
                    case 8:
                        return T_06;
                    case 9:
                        return T_09;
                    case 16:
                        return T_16;                        
                }
            }
        } else {
            if((rt==TA_EGI_1) || (rt==TA_EGI_2)) {
                switch(sa) {
                    case 1:
                        return T_01;
                    case 2:
                        return T_02;
                    case 3:
                        return T_03;
                    case 9:
                        return T_09;
                }
            }
        }
        return UNKNOWN;
    }
}
