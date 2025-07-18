/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.messages.tim4;

import _int.nato.ncia.natxmlib.clock.SystemClock;
import _int.nato.ncia.natxmlib.types.FieldType;

/**
 *
 * @author mike
 */
public class NATIM4_RequestReplyRecord {
    public static enum Format {
        NO_DATA,
        DATA_REQUEST,
        HOST_REPLY,
        ILLEGAL;
    }
    protected final Format format;

    protected NATIM4_RequestReplyRecord(Format format) {
        this.format = format;
    }

    public Format getFormat() {
        return format;
    }

    
    public static final FieldType<NATIM4_RequestReplyRecord> TYPE = new FieldType<NATIM4_RequestReplyRecord>() {
        @Override
        public int getLength() {
            return 32;
        }

        @Override
        public NATIM4_RequestReplyRecord decode(long code) {
            int formatCode = (int)(code>>30)&3;
//            System.out.println("### "+SystemClock.getInstance().now()+":"+formatCode);
            switch(formatCode) {
                case 0: return new NATIM4_RequestRepyRecord_Empty();
                case 1: return new NATIM4_RequestRepyRecord_Request(code);
                case 2: return new NATIM4_RequestRepyRecord_Reply(code);
            }
            throw new IllegalArgumentException();
        }

        @Override
        public long encode(NATIM4_RequestReplyRecord value) {
            switch(value.getFormat()) {
                case DATA_REQUEST: {
                    return ((NATIM4_RequestRepyRecord_Request)value).encode();
                }
                default:
                    throw new IllegalArgumentException();
                    
            }
        }

        @Override
        public String getText(NATIM4_RequestReplyRecord value) {
            return value.toString();
        }
        
    };
}
