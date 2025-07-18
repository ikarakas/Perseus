/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.ginslib;

import java.time.Duration;
import java.time.Instant;
import java.time.ZoneId;

/**
 *
 * @author mike
 */
public class GINSMessage {
    protected Instant systemReceiveTime;
    protected Duration hardwareTimeStamp;
    protected int source;
    public final static ZoneId UTC = ZoneId.of("UTC");
    protected String name;

    public GINSMessage(String name) {
        this.name = name;
    }
    public GINSMessage() {
        this(null);
    }
    
    public static boolean toBoolean(short wd, int offset) {
        return ((wd >> offset)&0x1)!=0;
    }
    public static int toSignedInt(short wd) {
        return GINSDecoder.toSigned32(wd);
    }
    public static int toUnsignedInt(short wd) {
        return GINSDecoder.toUnsigned32(wd);
    }

    public Instant getSystemReceiveTime() {
        return systemReceiveTime;
    }

    public void setSystemReceiveTime(Instant receiveTime) {
        this.systemReceiveTime = receiveTime;
    }

    public int getSource() {
        return source;
    }

    public void setSource(int source) {
        this.source = source;
    }

    public Duration getHardwareTime() {
        return hardwareTimeStamp;
    }

    public void setHardwareTime(Duration hardwareTimeStamp) {
        this.hardwareTimeStamp = hardwareTimeStamp;
    }

    public String getName() {
        return name;
    }
    
    
}
