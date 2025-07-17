/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.ginslib;

import java.time.Instant;
import java.time.ZoneId;
import java.time.ZonedDateTime;

/**
 *
 * @author mike
 */
public class GINS_T01 extends GINSMessage {
    protected boolean positionIncorporated;
    protected boolean inuValid;
    protected boolean gpsValid;
    protected boolean noGO;
    protected boolean alignInProgress;
    protected boolean alignComplete;
    protected boolean coarseAlignComplete;
        
    protected int timeOfAlignment;
    protected double alignQuality;
    
    protected boolean navDataValid;
    protected boolean utcValid;
    
    protected int gpsFOM;
    
    protected boolean messageAvailable;
    protected boolean dayReceived;
    protected boolean timeOfDayReceived;
    
    protected int year;
    protected int month;
    protected int day;
    protected double sec;
    
    public GINS_T01(short[] wd)  {
        super("T-01");
        positionIncorporated = ((wd[1]>>15) & 0x1) != 0;
        inuValid = ((wd[1]>>13) & 0x1) != 0;
        gpsValid = ((wd[1]>>12) & 0x1) != 0;
        noGO = ((wd[1]>>11) & 0x1) != 0;
        alignInProgress = ((wd[1]>>10) & 0x1) != 0;
        alignComplete = ((wd[1]>>9) & 0x1) != 0;
        coarseAlignComplete = ((wd[1]>>3) & 0x1) != 0;
        
        timeOfAlignment=GINSDecoder.toSigned32(wd[2]);
        alignQuality=GINSDecoder.toSigned32(wd[3])*Math.pow(2, -8);
        
        navDataValid=((wd[4]>>15) & 0x1) != 0;
        utcValid=((wd[4]>>7) & 0x1) != 0;
        
        messageAvailable=((wd[10]>>15) & 0x1) != 0;
        dayReceived=((wd[10]>>14) & 0x1) != 0;
        timeOfDayReceived=((wd[10]>>13) & 0x1) != 0;
        
        gpsFOM=wd[6] & 0xf;
        year = (int)wd[11];
        month = (int)wd[12];
        day = (int)wd[13];
        long secCode=GINSDecoder.toUnsigned32(wd[14], wd[15]);
        sec=secCode*6.1*Math.pow(10.0, -8);
        int y = 10;
    }
    public static GINS_T01 decode(short[] swords) {
        return new GINS_T01(swords);
    }
    

    public int getYear() {
        return year;
    }

    public int getMonth() {
        return month;
    }

    public int getDay() {
        return day;
    }
    public Instant toInstant() {
        ZonedDateTime zdt = ZonedDateTime.of(year, month, day, 0, 0, 0, 0, ZoneId.of("UTC"));
        return zdt.toInstant();
    }

    public boolean isPositionIncorporated() {
        return positionIncorporated;
    }

    public boolean isInuValid() {
        return inuValid;
    }

    public boolean isGpsValid() {
        return gpsValid;
    }

    public boolean isNoGO() {
        return noGO;
    }

    public boolean isAlignInProgress() {
        return alignInProgress;
    }

    public boolean isAlignComplete() {
        return alignComplete;
    }

    public boolean isCoarseAlignComplete() {
        return coarseAlignComplete;
    }

    public int getTimeOfAlignment() {
        return timeOfAlignment;
    }

    public double getAlignQuality() {
        return alignQuality;
    }

    public boolean isNavDataValid() {
        return navDataValid;
    }

    public boolean isUtcValid() {
        return utcValid;
    }

    public int getGpsFOM() {
        return gpsFOM;
    }

    public boolean isMessageAvailable() {
        return messageAvailable;
    }

    public boolean isDayReceived() {
        return dayReceived;
    }

    public boolean isTimeOfDayReceived() {
        return timeOfDayReceived;
    }

    public double getSec() {
        return sec;
    }
    
}
