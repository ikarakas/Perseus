/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.ginslib;

import _int.nato.ncia.ginslib.busmon.BusMonitorMessage;
import java.time.Instant;

/**
 *
 * @author mike
 */
public class GINSDecoder {
    // RX => RT TO BC
    // TX => BC TO RT
    // RX,TX => RT_TX TO RT_RX
    
    public static GINSMessage _decode(MessageType mt, BusMonitorMessage bm) {
        if(mt==MessageType.UNKNOWN) {
            return null;
        }
        if(bm.getLength()==0) {
            return null;
        }
        int[] le_words = new int[bm.getLength()];
        short[] swords=new short[bm.getLength()];
        short[] dwords=new short[bm.getLength()];
        
        for (int i = 0; i < le_words.length; i++) {
            le_words[i] = Short.toUnsignedInt(Short.reverseBytes((short) bm.getWords()[i]));
            swords[i] = Short.reverseBytes((short) bm.getWords()[i]);
            dwords[i] = (short) bm.getWords()[i];
        }
        switch(mt) {
            case T_01:
                return GINS_T01.decode(dwords);
            case T_02:
                return GINS_T02.decode(dwords);
            case T_04:
                return GINS_T04.decode(dwords);
            case T_06:
                return GINS_T06.decode(dwords);
            case R_01:
                return GINS_R01.decode(dwords);
            case T_09:
                return GINS_T09.decode(dwords);
            case T_16:
                return GINS_T16.decode(dwords);
            case T_20:
                return GINS_T20.decode(dwords);
            case T_27:
                return GINS_T27.decode(dwords);
        }
        return null;
    }

    public static GINSMessage decode(MessageType mt, BusMonitorMessage bm) {
        GINSMessage gm = null;
        try {
            gm = _decode(mt, bm);
        } catch (Throwable t) {
            System.err.println("Message decode failure:" + mt + "," + t);
        }

        if (gm != null) {
            Instant srt = Instant.ofEpochMilli(bm.getHostTimeStamp());
            gm.setSystemReceiveTime(srt);
            gm.setHardwareTime(bm.getHardwareChronoTimeStamp());
            gm.setSource((bm.isTransmit()?10000:0)+bm.getRT()*100+bm.getSA());
        }
        return gm;
    }

    public static int toSigned32(short sw) {
        return (int)sw;
    }
    public static int toUnsigned32(short sw) {
        return Short.toUnsignedInt(sw);
    }
        
    public static int toSigned32(int msw_16, int lsw_16) {
        return msw_16<<16|lsw_16;            
    }
    public static int toSigned32(short msw_16, short lsw_16) {
        return ((int)msw_16)<<16|Short.toUnsignedInt(lsw_16);
    }
    public static long toUnsigned32(int msw_16, int lsw_16) {
        return ((long)msw_16)<<16|lsw_16;            
    }
    public static long toUnsigned32(short msw_16, short lsw_16) {
        return ((long)Short.toUnsignedInt(msw_16))<<16 | Short.toUnsignedInt(lsw_16);           
    }
    
}
