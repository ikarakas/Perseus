/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.ginslib.raw;

import _int.nato.ncia.ginslib.busmon.BusMonitorMessage;
import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.time.Instant;
import java.util.List;
import java.util.function.Consumer;

/**
 *
 * @author mike
 */
public class RawFile {
    protected Path path;
    public RawFile(String fileName) throws IOException {
       path=Path.of(fileName);
    }
    protected String[] columnNames;
    
    public static void parse(String fileName, Consumer<Record> rc) throws IOException {
        List<String> lines = Files.readAllLines(Path.of(fileName));
        int lineIndex=0;
        for(String line : lines) {
            String[] cols=line.split("\t");
            if(lineIndex<2) {
                lineIndex++;
                continue;
            }
            if(lineIndex==2) {
                lineIndex++;
                continue;
            }
            Record rec=new Record(cols);
            rec.recLine=line;
            rc.accept(rec);
            lineIndex++;
            
        }  
        int y=10;
    }
    public static void readBusMessages(String fileName, Consumer<BusMonitorMessage> rc) throws IOException {
        List<String> lines = Files.readAllLines(Path.of(fileName));
        int lineIndex=0;
        for(String line : lines) {
            String[] cols=line.split("\t");
            if(lineIndex<2) {
                lineIndex++;
                continue;
            }
            if(lineIndex==2) {
                lineIndex++;
                continue;
            }
            Record rec=new Record(cols);
            rec.recLine=line;
            rc.accept(rec.toBusMonitorMessage(System.currentTimeMillis()));
            lineIndex++;            
        }  
        rc.accept(null);
        int y=10;
    }
    public static class Record {
        public long micros;
        public int dc;
        public int cwd1;
        public int cwd2;
        public int swd1;
        public int swd2;
        public int[] dw;
        public int cwd_1_rt;
        public boolean cwd_1_t;
        public int cwd_1_sa;
        public int cwd_1_wc;
        public int cwd_2_rt;
        public boolean cwd_2_t;
        public int cwd_2_sa;
        public int cwd_2_wc;
        public String recLine;
        
        public Record(String[] cols) {
            
            long tt_low=Long.parseLong(cols[1],16);
            long tt_high=Long.parseLong(cols[2],16);
            micros=((long)tt_high&0x7fffffffL)<<32|(tt_low&0xffffffffL);
            long secs=micros/1_000_000;
            long nanos=(micros*1000)%1_000_000;
            Instant time=Instant.ofEpochSecond(secs, nanos);
            
            dc=Integer.parseInt(cols[5],16);
            cwd1=Integer.parseInt(cols[7],16);
            cwd2=Integer.parseInt(cols[8],16);
            swd1=Integer.parseInt(cols[9],16);
            swd2=Integer.parseInt(cols[10],16);
            dw = new int[dc];
            for(int i=0;i<dw.length;i++) {
                dw[i]=Integer.parseInt(cols[12+i],16);
            }
            cwd_1_rt=getRT(cwd1);
            cwd_1_t=getT(cwd1)==1;
            cwd_1_sa=getSA(cwd1);
            cwd_1_wc=getWC(cwd1);
            cwd_2_rt=getRT(cwd2);
            cwd_2_t=getT(cwd2)==1;
            cwd_2_sa=getSA(cwd2);
            cwd_2_wc=getWC(cwd2);
        }
        public int getCwd1() {
            return cwd1;
        }

        public long getMicros() {
            return micros;
        }
        
        public BusMonitorMessage toBusMonitorMessage(long hostTimeStamp) {
            if((cwd_1_rt==2) && (!cwd_1_t)) {
                int y=10;
            }
            int[] le_words = new int[dw.length];
            for(int i=0;i<le_words.length;i++) {
               //le_words[i]=Short.toUnsignedInt(Short.reverseBytes((short)dw[i]));
               le_words[i]=Short.toUnsignedInt((short)dw[i]);
            }
            return new BusMonitorMessage(cwd_1_rt, cwd_1_sa, cwd_1_t, le_words, swd1, cwd1, 0, 0, micros, hostTimeStamp);
        }
        @Override
        public String toString() {
            String str1 = String.format("%s:%02d:%02d:%02d", (cwd_1_t?"T":"R"),cwd_1_rt,cwd_1_sa,cwd_1_wc);
            String str2 = String.format("%s:%02d:%02d:%02d", (cwd_2_t?"T":"R"),cwd_2_rt,cwd_2_sa,cwd_2_wc);
            String s3=String.format("(%s/%s/%02d)", str1,str2,dw.length);
            return s3;
        }
    }
    public static int getRT(int cwd) {
        return (cwd>>11)&0x1f;
    }
    public static int getT(int cwd) {
        return (cwd>>10)&0x1;
    }
    public static int getSA(int cwd) {
        return (cwd>>5)&0x1f;
    }
    public static int getWC(int cwd) {
        return cwd&0x1f;
    }
    
    
}
