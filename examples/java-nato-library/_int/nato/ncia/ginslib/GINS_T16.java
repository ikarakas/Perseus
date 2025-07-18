/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.ginslib;

import java.time.Instant;
import java.time.Year;

/**
 *
 * @author mike
 */
public class GINS_T16 extends GINSMessage {
    protected int timeFOM;
    protected int dayOfYear;
    protected int year;
    
    public GINS_T16(short[] wd)  {
        super("T-16");        
        year= 2000 + (wd[29] & 0x0f) + 10*((wd[29]>>4) & 0x0f);
        dayOfYear = ((wd[30] >> 4) & 0x0f) + 10*((wd[30]>>8) & 0x0f) + 100*((wd[30]>>12) & 0x0f);
        timeFOM=((wd[29]>>8) & 0x0f);
    }
    public Instant toStartOfDay() {
        return (Year.of(year).atDay(dayOfYear).atStartOfDay(UTC)).toInstant();
    }

    public int getTimeFOM() {
        return timeFOM;
    }

    public int getDayOfYear() {
        return dayOfYear;
    }

    public int getYear() {
        return year;
    }
    public static GINS_T16 decode(short[] swords) {
        if(swords.length==32) {
            return new GINS_T16(swords);
        }else{
            return null;
        }
    }
    
}
