/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.types;

import _int.nato.ncia.natxmlib.fields.TimeStamp;
import java.time.Instant;

/**
 *
 * @author mike
 */
public class TimeStampType implements FieldType<TimeStamp> {
    public final static long MIN_CODE=0;
    public final static long MAX_CODE=0xffffff;
    
    public final static TimeStamp MIN=fromCode(MIN_CODE);
    public final static TimeStamp MAX=fromCode(MAX_CODE);
        
    @Override
    public TimeStamp decode(long lcode) {
        return fromCode(lcode);
    }
    public final static TimeStamp fromCode(long lcode) {
        int code=(int)(lcode & 0xffffffL);
        int micros = (int)((code&0x3f)*15625);
        int tsec=(code>>6);
        int hrs=tsec/(60*60);
        tsec=tsec-hrs*60*60;
        int min=tsec/60;
        tsec=tsec-min*60;
        int sec=tsec;
        return new TimeStamp(hrs, min, sec, micros);
    }
    @Override
    public long encode(TimeStamp value) {
        int micros= (int)(value.getMicros()/15625)&0x3f;
        int sec=value.getHrs()*3600+value.getMin()*60+value.getSec();
        return micros | (sec<<6);        
    }

    @Override
    public int getLength() {
        return 24;
    }
    
}
