/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.ginslib;

import java.time.Duration;

/**
 *
 * @author mike
 */
public class GINS_R01 extends GINSMessage{
        int modeCode;
        boolean setPosition;
        int positionUpdateCode;
        boolean dayValid;
        boolean todValid;
        boolean fixedLatLngValid;
        boolean deltaLatLngValid;
        boolean egrReset;
        
    private GINS_R01(short[] wd) {
        modeCode = (wd[0] >> 12)&0xf;
        setPosition = ((wd[0] >> 6) & 01) != 0;
        positionUpdateCode = ((wd[0] >> 4) & 01);
        
        fixedLatLngValid=((wd[1] >> 12) & 01) != 0;
        deltaLatLngValid=((wd[1] >> 10) & 01) != 0;
        dayValid=((wd[1] >> 7) & 01) != 0;
        todValid=((wd[1] >> 6) & 01) != 0;
        egrReset=(wd[1] & 01) != 0;
        
        int latCode = GINSDecoder.toSigned32(wd[5],wd[6]);
        double latLsb=Math.pow(2, -31);
        double lat = latCode*latLsb*180.0;
        
        int lngCode = GINSDecoder.toSigned32(wd[6],wd[7]);
        double lngLsb=Math.pow(2, -31);
        double lng = lngCode*latLsb*180.0;
        
        int year = GINSDecoder.toUnsigned32(wd[11]);
        int month= GINSDecoder.toSigned32(wd[22]);
        int day= GINSDecoder.toSigned32(wd[23]);
        long scode = GINSDecoder.toUnsigned32(wd[24],wd[25]);
        double lsb=Math.pow(2, -14);
        double gmt_tod = scode*lsb;
        int y=10;
    }
    public static GINS_R01 decode(short[] words) {
        if(words.length!=32) {
            return null;
        }
        return new GINS_R01(words);
    }

}
