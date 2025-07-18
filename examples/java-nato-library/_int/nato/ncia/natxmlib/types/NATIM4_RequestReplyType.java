/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.types;

import _int.nato.ncia.natxmlib.messages.tim4.NATIM4_RequestReply;


/**
 *
 * @author mike
 */
public class NATIM4_RequestReplyType implements FieldType<NATIM4_RequestReply>{

    @Override
    public NATIM4_RequestReply decode(long code) {
        switch((int)code) {
            case 0:
                return NATIM4_RequestReply.NO_DATA;
            case 1:
                return NATIM4_RequestReply.DATA_REQUEST;
            case 2:
                return NATIM4_RequestReply.HOST_REPLY;
            case 3:
                return NATIM4_RequestReply.ILLEGAL;
            default:
                throw new IllegalArgumentException();
        }
    }

    @Override
    public long encode(NATIM4_RequestReply value) {
        switch(value) {
            case NO_DATA:
                return 0;
            case DATA_REQUEST:
                return 1;
            case HOST_REPLY:
                return 2;
            case ILLEGAL:                
                return 3;
        }
        throw new IllegalArgumentException();
    }

    @Override
    public int getLength() {
        return 2;
    }
    
}
