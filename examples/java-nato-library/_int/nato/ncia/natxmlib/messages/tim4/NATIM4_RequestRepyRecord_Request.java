/* 
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.messages.tim4;

/**
 *
 * @author mike
 */
public class NATIM4_RequestRepyRecord_Request extends NATIM4_RequestReplyRecord {
    protected AddressTypeSpecifier addressType;
    protected int addressExtension;
    protected int addressLocator; //0=SICP,1=ILLEGAL
    protected RequestType requestType;
    protected int wordCount;
    protected int addressWord;

    protected int startDataBlockId; //data word code
    protected int startDataWord;
    protected int dataWordCount;
    
    protected int address; //physical
    
    protected NATIM4_RequestRepyRecord_Request(long code) {
        super(Format.DATA_REQUEST);
        this.addressType=AddressTypeSpecifier.values()[(int)((code >> 28) & 0x3)];
        this.addressWord=(int)(code&0xffff);
        this.dataWordCount=(int)(code&0x1f);
        this.startDataWord=(int)((code>>5)&0x1f);
        this.startDataBlockId=(int)((code>>10)&0x3f);
        this.wordCount=(int)((code >> 16) & 0x1f);
        this.requestType=RequestType.values()[(int)((code >> 21) & 0x3)];
        this.addressLocator=(int)((code >> 23) & 0x1);
        this.addressExtension=(int)((code >> 24) & 0xf); 
        this.address=this.addressWord|(this.addressExtension<<16);
    }
    public long encode() {
        long code = format.ordinal()<<30;
        code|=addressType.ordinal()<<28;
        code|=(dataWordCount&0x1f);
        code|=(startDataWord&0x1f)<<5;
        code|=(startDataBlockId&0x3f)<<10;
        code|=(requestType.ordinal()<<21);
        code|=(wordCount&0x1f)<<16;
        return code;
    }

    public NATIM4_RequestRepyRecord_Request(RequestType rt, int startBlockId, int startWordId, int wordCount) {
        super(Format.DATA_REQUEST);
        this.addressType=AddressTypeSpecifier.DATA_WORD_CODE;
        this.requestType=rt;
        this.startDataBlockId=startBlockId;
        this.startDataWord=startWordId;
        this.dataWordCount=wordCount;
        this.addressLocator=0;
        this.address=0;
        this.addressExtension=0;
        this.addressWord=0;
    }
    public AddressTypeSpecifier getAddressType() {
        return addressType;
    }

    public RequestType getRequestType() {
        return requestType;
    }

    public int getStartDataBlockId() {
        return startDataBlockId;
    }

    public int getStartDataWord() {
        return startDataWord;
    }

    public int getDataWordCount() {
        return dataWordCount;
    }
    @Override
    public String toString() {
        if(addressType==AddressTypeSpecifier.DATA_WORD_CODE) {
            return "{" + "format=" + format + ", addressType=" + addressType +  ", requestType=" + requestType + ", startDataBlockId="+startDataBlockId +", startDataWord="+startDataWord +", dataWordCount=" + dataWordCount+"}";
        }else {
            return "{" + "format=" + format + ", addressType=" + addressType + ", address=" + address + ", al=" + addressLocator + ", requestType=" + requestType + ", wordCount=" +wordCount+ "}";
        }
    }
    public enum AddressTypeSpecifier {
        NOT_DEFINED_0x0,
        PHYSICAL,
        DATA_WORD_CODE,
        NOT_DEFINED_0x3;
    }
    public enum RequestType {
        NOT_DEFINED_0x0,
        ADDRESS_REQUEST,
        STATUS_REQUEST,
        INITIALIZATION_REQUEST,
    }
}
