/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.LinkedList;
import java.util.List;

/**
 *
 * @author mike
 */
public class DumpFile {
    public static LinkedList<Record> parse(String fileName) throws IOException {
        List<String> lines = Files.readAllLines(Path.of(fileName));
        LinkedList<Record> result = new LinkedList<>();
        int lineNumber=1;
        for(String line : lines) {
            if(line.length()>20) {
                result.add(new Record(line,lineNumber));
            }
            lineNumber++;
        }
        return result;
    }
    public static class Record implements JTIDSDataFrame{
        protected Instant time;
        protected  int[] words;
        protected boolean tim;
        protected String line;
        protected int lineNumber;
        
        public Record(String line, int lineNumber) {
            String tstr=Instant.now().toString();
            String dstr = tstr.substring(0, tstr.indexOf("T"));
            String istr=dstr+"T"+line.substring(0, 14)+"Z";
            this.time=Instant.parse(istr);
            this.words=new int[9];
            String wlist=line.substring(26).replace("  ", " ");
            for(int i=0;i<words.length;i++) {
                String wstr = wlist.substring(i*9, i*9+8);
                words[i]=(int)(Long.parseLong(wstr, 16) & 0xffffffff);
            }
            String format = line.substring(18, 22);
            this.tim=format.startsWith("TIM");
            this.line=line;
            this.lineNumber=lineNumber;
        }
        @Override
        public byte[] getBytes() {
            byte[] data = new byte[9*Integer.BYTES];
            ByteBuffer bb = ByteBuffer.wrap(data).order(ByteOrder.BIG_ENDIAN);
            for(int w : words) {
                bb.putInt(w);
            }
            return data;
        }

        @Override
        public int getWord(int idx) {
            return words[idx];
        }

        @Override
        public void setWord(int idx, int wvalue) {
            throw new UnsupportedOperationException("Not supported yet."); // Generated from nbfs://nbhost/SystemFileSystem/Templates/Classes/Code/GeneratedMethodBody
        }

        public Instant getTime() {
            return time;
        }

        public boolean isTIM() {
            return tim;
        }

        public int getLineNumber() {
            return lineNumber;
        }
        
        @Override
        public String toString() {
            StringBuilder sb = new StringBuilder();
            for (int i = 0; i < words.length; i++) {
                sb.append(String.format("%08X", words[i]));
                sb.append(" ");
            }
            return sb.toString().trim();
        }
        
    }    
}
