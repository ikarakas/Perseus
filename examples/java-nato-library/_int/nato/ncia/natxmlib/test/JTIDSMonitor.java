/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.test;

import _int.nato.ncia.natxmlib.JTIDSDataFrameSource;
import _int.nato.ncia.natxmlib.NATOMReader;
import _int.nato.ncia.natxmlib.clock.SystemClock;
import _int.nato.ncia.natxmlib.messages.NATxM;
import _int.nato.ncia.natxmlib.messages.tom1.NATOM01;
import _int.nato.ncia.natxmlib.messages.tom1.NATOM01.DataBlock;
import _int.nato.ncia.natxmlib.messages.tom4.NATOM04;
import _int.nato.ncia.natxmlib.types.Field;
import _int.nato.ncia.natxmlib.types.GenericMessageField;
import java.io.IOException;
import java.util.Map;
import java.util.logging.Level;
import java.util.logging.Logger;

/**
 *
 * @author mike
 */
public class JTIDSMonitor {
    protected final JTIDSDataFrameSource bimSource;
    protected final JTIDSDataFrameSource bomSource;

    public JTIDSMonitor(JTIDSDataFrameSource bimSource, JTIDSDataFrameSource bomSource) {
        this.bimSource = bimSource;
        this.bomSource=bomSource;
    }
    protected Thread bomReaderThread;
    
    public void start() {
        bomReaderThread=new Thread(new ReaderRunnable());
        bomReaderThread.setName("TOMReader");
        bomReaderThread.start();
    }
    public void stop() {
        bomReaderThread.interrupt();
    }
    public void run() {
        bomReaderThread=new Thread(new ReaderRunnable());
        bomReaderThread.setName("TOMReader");
        bomReaderThread.run();
    }
    protected JTIDSInitData initData = new JTIDSInitData();
    protected JTIDSStatusData statusData = new JTIDSStatusData();
    
   
  
    protected void onTOM01(NATOM01 tom01) {
        for(DataBlock db : tom01.getDatablocks()) {
            switch(db.getControlWord().getResponseTypeCode()) {
                case 2:
                    Map<String, Long> fcmap0 = statusData.getFieldCodes();
                    statusData.setWords(db.getBlockId(), db.getStartingDataWord(), db.getDataWords());
                    System.out.print(SystemClock.getInstance().now()+":JM:STATUS_DATA_REPORT: blkId="+db.getBlockId()+", wordId="+db.getStartingDataWord()+", words=");
                    for(int i=0;i<db.getDataWords().length;i++) {
                        System.out.print(String.format("0x%04x ",db.getDataWords()[i]));
                    }
                    System.out.println();
/*                    Map<String, Long> fcmap1 = statusData.getFieldCodes();
                    for(String fname : fcmap0.keySet()) {
                        Long v0 = fcmap0.get(fname);
                        Long v1 = fcmap1.get(fname);
                        if(v1!=v0) {
                            System.out.println("STATUS_DATA_UPDATE:"+fname+"="+v1+" (before:"+v0+")");
                        }
                    }
*/
                    break;
                case 3:
                    initData.setWords(db.getBlockId(), db.getStartingDataWord(), db.getDataWords());
                    System.out.print(SystemClock.getInstance().now()+":JM:INIT_DATA_REPORT: blkId="+db.getBlockId()+", wordId="+db.getStartingDataWord()+", words=");
                    for(int i=0;i<db.getDataWords().length;i++) {
                        System.out.print(String.format("0x%04x ",db.getDataWords()[i]));
                    }
                    System.out.println();
                    break;
                default:
                    int y=10;
                    break;
            }
        }
    }
    protected void onTOM04(NATOM04 tom) {
        StringBuilder sb = new StringBuilder();
        for(Field f : tom.fields()) {
            if(f.getCode()!=0) {
                sb.append(" /");
                sb.append(((GenericMessageField)f).getName());
                sb.append("=");
                sb.append(f.getValue().toString());
            }
        }
        System.out.println(SystemClock.getInstance().now()+":JTM:TOM4:"+sb.toString());
    }
    protected void onTOM(NATxM tom) throws Exception {
        if (tom instanceof NATOM01) {
            onTOM01((NATOM01)tom);
        }else if(tom instanceof NATOM04) {
            onTOM04((NATOM04)tom);
        }
    }
   
    public class ReaderRunnable implements Runnable {

        NATOMReader reader = new NATOMReader(bomSource);

        @Override
        public void run() {
            while (!Thread.interrupted()) {
                NATxM tom = null;
                try {
                    tom = reader.read();
                    if (tom == null) {
                        break;
                    }
                } catch (IOException ex) {
                    Logger.getLogger(JTIDSMonitor.class.getName()).log(Level.SEVERE, null, ex);
                    break;
                } catch (IllegalArgumentException iaex) {
                    Logger.getLogger(JTIDSMonitor.class.getName()).log(Level.WARNING, null, iaex);
                }
                if (tom != null) {
                    try {
                        onTOM(tom);
                    } catch (IOException ex) {
                        Logger.getLogger(JTIDSMonitor.class.getName()).log(Level.SEVERE, null, ex);
                        break;

                    } catch (Exception ex) {
                        Logger.getLogger(JTIDSMonitor.class.getName()).log(Level.WARNING, null, ex);
                    }
                }
            }
        }
    }
}
