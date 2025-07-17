/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.test;

import _int.nato.ncia.natxmlib.JTIDSDataFrame;
import _int.nato.ncia.natxmlib.JTIDSDataFrameSource;
import _int.nato.ncia.natxmlib.NATIMReader;
import _int.nato.ncia.natxmlib.NATOMReader;
import _int.nato.ncia.natxmlib.conversion.JDataConverter;
import _int.nato.ncia.natxmlib.fields.TimeStamp;
import _int.nato.ncia.natxmlib.messages.NATxM;
import _int.nato.ncia.natxmlib.messages.common.JWordData;
import _int.nato.ncia.natxmlib.messages.common.SubgroupData;
import _int.nato.ncia.natxmlib.messages.tim3.NATIM03;
import _int.nato.ncia.natxmlib.messages.tom3.NATOM03;
import aocslib.dataelements.Link16;
import aocslib.dataelements.Link16Word;
import java.io.IOException;
import java.time.Instant;
import java.util.logging.Level;
import java.util.logging.Logger;
import tdllib.link16.data.Link16WordData;

/**
 *
 * @author mike
 */
public class CoderTest {
    public static byte[] encode(Link16 de) {
        byte[] data = new byte[32+de.getContentSize()];
        de.putTo(data, 0);
        return data;
    }
    public static Link16 randomLink16() {
        aocslib.dataelements.Link16Word[] l16w = new Link16Word[1 + (int) (Math.ceil(Math.random() * 11))];
        for (int i = 0; i < l16w.length; i++) {
            aocslib.dataelements.Link16Word w = new aocslib.dataelements.Link16Word();
            for (int j = 0; j < 70; j++) {
                w.set(j, ((int) (Math.random() * 256)) % 2 == 0);
            }
            l16w[i] = w;
        }
        int stn=(int)(Math.ceil(Math.random()*((1<<15)-1)));
        Link16 l16 = new Link16(stn, l16w);
        return l16;
    }
    public static NATOM03 toTOM03(Link16 l16, int npg, TimeStamp ts) {
        JWordData[] jwd = JDataConverter.toJWordData(l16.getWords());
        SubgroupData[] sg = JDataConverter.toSubgroupData(jwd);
        Instant now = Instant.now();
        NATOM03 tom03 = NATOM03.create(l16.getSource(), 0, TimeStamp.fromInstant(now), sg);
        return tom03;
    }
    public static NATIM03 toTIM03(Link16 l16, int npg, TimeStamp ts) {
        JWordData[] jwd = JDataConverter.toJWordData(l16.getWords());
        SubgroupData[] sg = JDataConverter.toSubgroupData(jwd);
        Instant now = Instant.now();
        return null;
    }
    public static NATxM decodeTOM(JTIDSDataFrame[] frames) throws IOException {
        JTIDSDataFrameSource fs = new JTIDSDataFrameSource() {
            int idx = 0;

            @Override
            public JTIDSDataFrame read() throws IOException {
                if (idx >= frames.length) {
                    return null;
                }
                return frames[idx++];
            }

            @Override
            public void close() {
            }
        };
        NATOMReader natr = new NATOMReader(fs);
        NATxM tom = natr.read();
        assert natr.read()==null;
        return tom;
    }
     public static NATxM decodeTIM(JTIDSDataFrame[] frames) throws IOException {
        JTIDSDataFrameSource fs = new JTIDSDataFrameSource() {
            int idx = 0;

            @Override
            public JTIDSDataFrame read() throws IOException {
                if (idx >= frames.length) {
                    return null;
                }
                return frames[idx++];
            }

            @Override
            public void close() {
            }
        };
        NATIMReader natr = new NATIMReader(fs);
        NATxM tim = natr.read();
        assert natr.read()==null;
        return tim;
    }
    public static boolean testAOCSLink16ToTOM03() throws IOException {
        Link16 l16 = randomLink16();
        Instant now = Instant.now();
        NATOM03 tom03 = toTOM03(l16, 0, TimeStamp.fromInstant(now));
        JTIDSDataFrame[] frames = tom03.encode();
        NATOM03 xtom03 = (NATOM03)decodeTOM(frames);
        JTIDSDataFrame[] xframes = xtom03.encode();
        if(xframes.length!=frames.length) {
            return false;
        }
        for(int i=0;i<xframes.length;i++) {
            for(int j=0;j<9;j++) {
                if(frames[i].getWord(j)!=xframes[i].getWord(j)) {
                    return false;
                }
            }
        }
        Link16WordData[] l16data = JDataConverter.getLink16WordData(xtom03.getData());
        Link16Word[] awords = JDataConverter.toAOCSLink16Words(l16data);
        Link16 xl16 = new Link16(xtom03.getSTN(), awords);
        byte[] d0=encode(l16);
        byte[] d1=encode(xl16);
        if(d0.length!=d1.length) {
            return false;                    
        }
        for(int i=32;i<d0.length;i++) {
            if(d0[i]!=d1[i]) {
                return false;
            }
        }
        return true;
    }
    public static void main(String[] args) {
        for(int i=0;i<10_000_000;i++) {
            try {
                if(!testAOCSLink16ToTOM03()) {
                    System.out.println("failed");
                    break;
                }
            } catch (IOException ex) {
                Logger.getLogger(CoderTest.class.getName()).log(Level.SEVERE, null, ex);
                break;
            }
        }
    }
}
