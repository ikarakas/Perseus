/*
 * Copyright (c) 2004 - 2012 NAMSA CSI Cell. All rights reserved.
 * 
 * The NAMSA CSI Cell is the copyright holder of all code below.
 * Do not copy, re-use or modify without permission.
 * 
 * NATO Unclassified.
 */
package _int.nato.ncia.ginslib.busmon;

import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.Duration;
import java.time.Instant;
import java.util.Arrays;

/**
 *
 * @author mkroe
 */
/*
 * unsigned long cwd:16;
  unsigned long sdw:16;
  
  unsigned long empty:1;
  unsigned long spare:3;
  unsigned long channel:4;
  unsigned long core:4;
  unsigned long card:4;
  unsigned long error:16;
  
  unsigned long activity:16;
  unsigned long spare_2:16;
  
  unsigned long sec:32;

  unsigned long usec:32;

  unsigned long hwts:32;
*/
public class BusMonitorMessage {
    protected final static boolean newFormat = true;
    
    protected final int card;
    protected final int core;
    protected final int channel;
    protected final int rt;
    protected final int sa;
    protected final boolean tx;
    protected final int[] words;
    protected final int sdw;
    protected final int cwd;
    protected final int error;
    protected final int activity;
    protected long  hostTimeStamp;
    protected long  hardwareTimeStamp;
    protected long hostTime_sec;
    protected long hostTime_microSec;
    
    public BusMonitorMessage(ByteBuffer bb) {
        long w0 = readUINT32_long(bb);
        long w1 = readUINT32_long(bb);
        long w2 = newFormat?readUINT32_long(bb):0;
        long w3 = readUINT32_long(bb);
        long w4 = readUINT32_long(bb);
        long w5 = readUINT32_long(bb);
        this.cwd = (int)(w0 & 0xffff);
        int wc = cwd&0x1f;
        this.sa= (cwd>>5)&0x1f;
        this.tx= ((cwd>>10)&0x1)!=0;
        this.rt= (cwd>>11)&0x1f;        
        this.sdw=(int)(w0>>16)&0xffff;
        boolean empty = (w1 &0x1)!=0;
        this.channel=(int)((w1>>4)&0xf);
        this.core=(int)((w1>>8)&0xf);
        this.card=(int)((w1>>12)&0xf);
        this.error = (int)((w1>>16)&0xffff);
        this.activity = (int)(w2&0xffff);
        this.hostTimeStamp=(w3)*1000+(w4)/1000;
        this.hostTime_sec=w3;
        this.hostTime_microSec=w4%1_000_000;
        this.hardwareTimeStamp=w5;
        this.words=new int[wc>0?wc:32];
        if(empty) {
            Arrays.fill(this.words, 0);
        }else{
            for(int i=0;i<words.length;i++) {
                int word = readUSHORT(bb);
                words[i]=word;
            }
        }
    }

    public BusMonitorMessage(int rt, int sa, boolean tx, int[] words, int sdw, int cwd, int error, int activity, long hardwareTimeStamp, long hostTimeStamp) {
        this.card=0;
        this.core=0;
        this.channel=0;
        this.rt = rt;
        this.sa = sa;
        this.tx = tx;
        this.words = words;
        this.sdw = sdw;
        this.cwd = cwd;
        this.error = error;
        this.activity = activity;
        this.hardwareTimeStamp = (hardwareTimeStamp & 0xffffffffL);
        this.hostTimeStamp=hostTimeStamp;
    }
    public byte[] toBytes() {
        boolean empty = true;
        for(int i=0;i<words.length;i++) {
            if(words[i]!=0) {
                empty=false;
                break;
            }
        }
        ByteBuffer bb = ByteBuffer.allocate(6*Integer.BYTES+(empty?0:words.length*Short.BYTES)).order(ByteOrder.LITTLE_ENDIAN);
        int w0 = cwd | sdw<<16;
        int w1 = (channel<<4)|(core<<8)|(card<<12)|(error<<16)|(empty?0x1:0);
        int w2 = (error<<16)|(activity);
        int w3 = (int)(hostTimeStamp/1000);
        int w4 = (int)(hostTimeStamp%1000)*100;
        int w5 = (int)hardwareTimeStamp;
        
        bb.putInt(w0);
        bb.putInt(w1);
        bb.putInt(w2);
        bb.putInt(w3);
        bb.putInt(w4);
        bb.putInt(w5);
        if(!empty) {
            for(int i=0;i<words.length;i++) {
                bb.putShort((short)words[i]);
            }
        }
        return bb.array();
    }
    public static int readUBYTE(ByteBuffer bb) {
        byte b = bb.get();
        if(b<0) {
            return 256+(int)b;
        }else{
            return b;
        }
    }
    public static int   readUSHORT(ByteBuffer bb) {
        int b0=readUBYTE(bb);
        int b1=readUBYTE(bb);
        return b0+b1*256;
        
    }
    public static int   readUINT32(ByteBuffer bb) {
        int b0=readUBYTE(bb);
        int b1=readUBYTE(bb);
        int b2=readUBYTE(bb);
        int b3=readUBYTE(bb);
        return b0+b1*0x100+b2*0x10000+b3*0x1000000;
        
    }
    public static long   readUINT32_long(ByteBuffer bb) {
        long b0=readUBYTE(bb);
        long b1=readUBYTE(bb);
        long b2=readUBYTE(bb);
        long b3=readUBYTE(bb);
        return b0+b1*0x100+b2*0x10000+b3*0x1000000;
        
    }
    public static   byte    getByte(int bval) {
        if(bval>=128) {
            return (byte)(bval-256);
        }else{
            return (byte)bval;
        }
    }   
    
    public  int getLength() {
        return words.length;
    }
    public  boolean isTransmit() {
        return tx;                
    }

    public int getCard() {
        return card;
    }

    public int getChannel() {
        return channel;
    }

    public int getCore() {
        return core;
    }

    public int getRT() {
        return rt;
    }

    public int getSA() {
        return sa;
    }
    public int getError() {
        return error;        
    }
    public int[] getWords() {
        return words;
    }
  
    public long getHostTimeStamp() {
        return hostTimeStamp;
    }
    public Instant getHostTime() {
        return Instant.ofEpochSecond(hostTime_sec,hostTime_microSec*1000);
    }
    public void setHostTimeStamp(long ts) {
        this.hostTimeStamp=ts;
    }
    public long getHardwareTimeStamp() {
        return hardwareTimeStamp;
    }
    public Instant getHardwareTime() {
        return Instant.ofEpochMilli(0).plus(Duration.ofNanos(hardwareTimeStamp*1000L));
    }
    public Duration getHardwareChronoTimeStamp() {
        return Duration.ofNanos(hardwareTimeStamp*1000L);
    }
    @Override
    public String toString() {
        String hdr = String.format("cd=%d, ch=%d, rt=%2d, sa=%2d, tx=%1d, len=%2d, hwtime=%12d, htime=%d, cwd=0x%04x, sdw=0x%04x",card, channel, rt,sa,tx?1:0,words.length,hardwareTimeStamp,hostTimeStamp,cwd,sdw);
        final StringBuilder sb = new StringBuilder(hdr.length() + 6 * words.length + 3)
                .append(hdr).append(" [");
        for (int word : words) {
            sb.append(String.format("0x%04x ", word));
        }
        sb.append(']');
        return sb.toString();
    }
    
}
