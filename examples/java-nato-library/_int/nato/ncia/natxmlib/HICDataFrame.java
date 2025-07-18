/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.Arrays;

/**
 *
 * @author mike
 */
public class HICDataFrame implements JTIDSDataFrame {
    public static final int WORD_LENGTH = 9;
    public static final int BYTE_LENGTH = WORD_LENGTH*Integer.BYTES;
    protected int[] words = new int[WORD_LENGTH];
    
    public HICDataFrame() {
        Arrays.fill(words, 0);
    }
    @Override
    public byte[]  getBytes() {
        byte[] data = new byte[BYTE_LENGTH];
        int didx=0;
        for(int i=0;i<words.length;i++) {
            for(int j=0;j<4;j++,didx++) {
                data[didx] = (byte)((words[i]>>(j*8))&0x00ff);
            }
        }
        return data;
    }
    public static HICDataFrame create() {
           return new HICDataFrame();
           
    }
    public static HICDataFrame fromBytes(byte[] arr, int ofs, int len) {
        HICDataFrame frame = new HICDataFrame();
        int didx=ofs;
        for(int i=0;i<WORD_LENGTH;i++) {
            for(int j=0;j<4;j++,didx++) {
                frame.words[i] |= (Byte.toUnsignedInt(arr[didx])<<(j*8));
            }
        }
        return frame;
    }    
    public static HICDataFrame fromWords(int[] words) {
        HICDataFrame frame = new HICDataFrame();
        if(words.length!=WORD_LENGTH) {
            throw new IllegalArgumentException();            
        }
        for(int i=0;i<WORD_LENGTH;i++) {
            frame.words[i]=words[i];
        }
        return frame;
    }    
    public static HICDataFrame read(InputStream ins) throws IOException {
        byte[] buffer = new byte[BYTE_LENGTH];
        ins.readNBytes(buffer, 0, BYTE_LENGTH);
        return fromBytes(buffer, 0, BYTE_LENGTH);
    }
    public void write(OutputStream outs) throws IOException {
        outs.write(getBytes());
    }
    @Override
    public int getWord(int idx) {
        return words[idx];
    }
    @Override
    public void setWord(int idx, int value) {
        this.words[idx]=value;
    }

    @Override
    public String toString() {
        StringBuilder sb=new StringBuilder();
        for(int i=0;i<words.length;i++) {
            sb.append(String.format("%08X", words[i]));
            sb.append(" ");
        }
        return sb.toString().trim();
    }
    
}
