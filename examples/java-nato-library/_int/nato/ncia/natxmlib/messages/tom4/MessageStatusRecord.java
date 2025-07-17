/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.messages.tom4;

import _int.nato.ncia.natxmlib.types.FieldType;

/**
 *
 * @author mike
 */
public class MessageStatusRecord {

    int rcCode;
    protected MessageStatus messageStatus;
    int loopbackId;

    public MessageStatusRecord(int rcCode, int messageStatusCode, int loopbackId) {
        this.rcCode = rcCode;
        this.messageStatus = MessageStatus.values()[messageStatusCode];
        this.loopbackId = loopbackId;
    }

    public MessageStatus getMessageStatus() {
        return messageStatus;
    }

    public int getLoopbackId() {
        return loopbackId;
    }
    
    @Override
    public String toString() {
        return "{" + "rcCode=" + rcCode + ", messageStatus=" + messageStatus + ", loopbackId=" + loopbackId + '}';
    }
    
    public static FieldType<MessageStatusRecord> TYPE = new FieldType<>() {
        @Override
        public int getLength() {
            return 32;
        }

        @Override
        public MessageStatusRecord decode(long code) {
            return new MessageStatusRecord(
                    (int)((code>>28) & 0xf),
                    (int)((code>>16) & 0x1f),
                    (int)(code & 0xfff)
            );
        }

        @Override
        public long encode(MessageStatusRecord value) {
            return ((value.rcCode & 0xf)<<28) | ((value.messageStatus.ordinal() & 0x1f)<<16) | ((value.loopbackId & 0xfff)) ;
        }
    };
    public enum MessageStatus {
        TRANSMITTED_OK,
        TRANSMITTED_LOOPBACK_ERROR,
        TRANSMITTED_TOA_ERROR,
        TRANSMITTED_NO_LOOPBACK,
        RC_REPLY_RECEIVED,
        ILLEGAL_5,
        RC_REPLY_NOT_RECEIVED,
        NICP_REJECTED_NO_VALID_SLOT_ASSIGNMENT,
        NICP_REJECTED_BUFFERS_FULL,
        NICP_REJECTED_IPF_PACKING_LIMIT_EXCEEDED,
        NICP_REJECTED_MISC, //10
        SICP_REJECTED,
        SICP_REJECTED_NPG_NOT_AVAILABLE,
        SICP_REJECTED_NOT_IN_FINE_SYNC,
        SICP_REJECTED_RADIO_OR_DATA_SILENT,
        SICP_REJECTED_PACKING_LIMIT_CONFLICT, //15
        SICP_REJECTED_CCP_NOT_INITIALIZED,
        SICP_REJECTED_CCP_BUFFERS_FULL,
        SICP_REJECTED_CCP_SKIPPED_CONVERSION,
        SICP_REJECTED_FREETEXT_MESSAGE_WITHOUT_NPG,
        SICP_REJECTED_STALENESS_EXCEEDED, //20
        SICP_REJECTED_CCPCP_FAILED, 
        SICP_REJECTED_INCOMPLETE_MULTIBLOCK_TRANSFER, 
        SICP_REJECTED_REPEAT_TRANSMISSION_BUFFERS_FULL, 
        SICP_REJECTED_MESSAGE_NOT_REPEATABLE, 
        ILLEGAL_25, 
        ILLEGAL_26, 
        ILLEGAL_27, 
        ILLEGAL_28, 
        ILLEGAL_29, 
        ILLEGAL_30, 
        ILLEGAL_31
    }
}