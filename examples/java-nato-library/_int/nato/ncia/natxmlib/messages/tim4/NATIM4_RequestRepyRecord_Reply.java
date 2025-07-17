/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.messages.tim4;

/**
 *
 * @author mike
 */
public class NATIM4_RequestRepyRecord_Reply extends NATIM4_RequestReplyRecord {
    protected int rcReplyCode;
    protected int rcLoopbackId;

    public NATIM4_RequestRepyRecord_Reply() {
        super(Format.HOST_REPLY);
    }
    protected NATIM4_RequestRepyRecord_Reply(long code) {
        super(Format.HOST_REPLY);
        this.rcLoopbackId=(int)(code & 0xfff);
        this.rcReplyCode=(int)((code >> 16) & 0x1f);
    }

    public int getRCReplyCode() {
        return rcReplyCode;
    }

    public int getRCLoopbackId() {
        return rcLoopbackId;
    }

    @Override
    public String toString() {
        return "{" + "format=" + format + ", rcReplyCode=" + rcReplyCode + ", rcLoopbackId=" + rcLoopbackId + "}";
    }
    
}
