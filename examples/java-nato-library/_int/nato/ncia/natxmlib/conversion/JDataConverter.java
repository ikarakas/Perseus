package _int.nato.ncia.natxmlib.conversion;

import _int.nato.ncia.natxmlib.fields.TimeStamp;
import _int.nato.ncia.natxmlib.messages.common.JWordData;
import _int.nato.ncia.natxmlib.messages.common.SubgroupData;
import _int.nato.ncia.natxmlib.messages.tim3.NATIM03;
import fxmlib.fields.TimeTag;
import fxmlib.fxm.FIM01;
import fxmlib.fxm.FIM01_Link16;
import fxmlib.fxm.Link16Word;
import java.util.LinkedList;
import tdllib.common.datafields.DataItemException;
import tdllib.link16.data.GenericLink16WordData;
import tdllib.link16.data.Link16WordData;
import tdllib.link16.decoder.Link16Variant;
import tdllib.link16.decoder.MessageDecoderFactory;
import tdllib.link16.messages.Message;
import tdllib.link16.words.Word;

/**
 *
 * @author mike
 */
public class JDataConverter {

    public static Link16Word toLink16Word(JWordData jwd) {
        Link16Word l16w = new Link16Word();
        for (int i = 0; i < 70; i++) {
            l16w.set(i, jwd.isBitSet(i));
        }
        return l16w;
    }

    public static Link16Word[] toLink16Words(SubgroupData[] arr) {
        LinkedList<Link16Word> wlist = new LinkedList<>();
        for (SubgroupData data : arr) {
            if (data instanceof JWordData) {
                wlist.add(toLink16Word((JWordData) data));
            }
        }
        return wlist.toArray(new Link16Word[0]);
    }

    public static Link16WordData toLink16WordData(JWordData jwd) {
        Link16WordData l16w = new GenericLink16WordData();
        for (int i = 0; i < 70; i++) {
            l16w.set(i, jwd.isBitSet(i));
        }
        return l16w;
    }

    public static Link16WordData[] getLink16WordData(SubgroupData[] arr) {
        LinkedList<Link16WordData> wlist = new LinkedList<>();
        for (SubgroupData data : arr) {
            if (data instanceof JWordData) {
                wlist.add(toLink16WordData((JWordData) data));
            }
        }
        return wlist.toArray(new Link16WordData[0]);
    }
    public static aocslib.dataelements.Link16Word[] toAOCSLink16Words(Message l16m) {
        LinkedList<Link16WordData> wdlist = new LinkedList<>();
        for(Word w : l16m.getWords()) {
            GenericLink16WordData gwd = new GenericLink16WordData();
            w.code(gwd);
            wdlist.add(gwd);
        }
        return toAOCSLink16Words(wdlist.toArray(new Link16WordData[0]));
    }
            
    public static aocslib.dataelements.Link16Word[] toAOCSLink16Words(Link16WordData[] arr) {
        aocslib.dataelements.Link16Word[] awords = new aocslib.dataelements.Link16Word[arr.length];
        for(int i=0;i<arr.length;i++) {
            awords[i]=new aocslib.dataelements.Link16Word();
            for(int j=0;j<70;j++) {
                awords[i].set(j, arr[i].get(j));
            }
        }
        return awords;
    }

    public static Iterable<Message> decode(Link16WordData[] wdarr) {
        LinkedList<Message> mlist = new LinkedList<>();

        for (int i = 0; i < wdarr.length;) {

            int wf = wdarr[i].getWordFormat();
            if (wf != 0) {
                throw new IllegalArgumentException();
            }
            int mli = wdarr[i].getMessageLengthIndicator();

            try {
                Message msg = MessageDecoderFactory.getMessageDecoder(Link16Variant.STANAG).decodeMessageData(wdarr, i, wdarr[i].getMessageLengthIndicator() + 1);
                mlist.add(msg);
            } catch (DataItemException ex) {
                throw new IllegalArgumentException(ex);
            }
            i += (wdarr[i].getMessageLengthIndicator() + 1);
        }
        return mlist;
    }

    public static Iterable<Message> decode(SubgroupData[] arr) {
        return decode(getLink16WordData(arr));
    }
    public static JWordData toJWordData(aocslib.dataelements.Link16Word al16wd) {
        JWordData result = new JWordData();
        for(int i=0;i<70;i++) {
            result.setBit(i, al16wd.get(i));
        }
        return result;
    }
    public static JWordData[] toJWordData(aocslib.dataelements.Link16Word[] al16wd) {
        JWordData[] result = new JWordData[al16wd.length];
        for(int i=0;i<result.length;i++) {
            result[i]=toJWordData(al16wd[i]);
        }
        return result;
    }
    public static JWordData toJWordData(fxmlib.fxm.Link16Word fword) {
        JWordData result = new JWordData();
        for(int i=0;i<70;i++) {
            result.setBit(i, fword.get(i));
        }
        return result;        
    }
    public static JWordData[] toJWordData(fxmlib.fxm.Link16Word[] fwords) {
        JWordData[] result = new JWordData[fwords.length];
        for(int i=0;i<result.length;i++) {
            result[i]=toJWordData(fwords[i]);
        }
        return result;        
    }
    
    public static SubgroupData[] toSubgroupData(JWordData[] jwd) {
        SubgroupData[] result = new SubgroupData[jwd.length];
        for(int i=0;i<result.length;i++) {
            result[i]=jwd[i];
        }
        return result;
        
    }
    public static FIM01 toFIM01(NATIM03 tim, TimeTag timeTag) {
        Link16Word[] l16words = toLink16Words(tim.getData());
        int rcid = 0;
        int msgid = tim.getLoopbackId() & 0x7ff;
        TimeStamp ts = tim.getTime();
//        TimeTag timeTag = new TimeTag(ts.getMin(), ts.getSec(), ts.getMs(), 0);
        boolean er = tim.getExtrapolationRequest();

        int reprom_request = tim.getRepromRequired() ? 1 : 0;
        int rc = tim.getReceiptCompliance() ? 1 : 0;
        int extrapolation_request = tim.getExtrapolationRequest() ? 1 : 0;
        int stn = tim.getSTN();
        int packingLimit = tim.getPackingLimit().ordinal();
        int priority = tim.getPriority();
        int sl = tim.getStalenessLimit();
        int sl_seconds = 0;
        if ((sl >= 1) && (sl <= 16)) {
            sl_seconds = sl;
        } else if ((sl > 16) && (sl < 31)) {
            sl_seconds = (sl - 15) * 16;
        } else if (sl == 31) {
            sl_seconds = 255;
        }
        int num_tx = tim.getNumberOfRepeatedTransmissions();
        int tx_rrn = 0;
        if ((num_tx > 0) || tim.getRepromRequired()) {
            int rr = tim.getRepeatedTransmissionRecurrencyRate();
            switch (rr) {
                case 0:
                    tx_rrn = 8;
                    break;
                case 1:
                    tx_rrn = 9;
                    break;
                case 2:
                    tx_rrn = 10;
                    break;
                case 3:
                    tx_rrn = 11;
                    break;
                case 4:
                    tx_rrn = 12;
                    break;
                default:
                    throw new IllegalArgumentException("invalid recurrency rate");
            }
        }
        int stalenessLimit = (int) Math.min(((double) sl_seconds / 0.0078125), 16383.0);
        int slot_selection_word = tim.getNPG();
        int reprom_rr = 0;
        int reprom_counter = 0;
        if (tim.getRepromRequired()) {
            reprom_rr = tx_rrn;
            reprom_counter = tim.getRepromCount();
        }
        FIM01 fim = new FIM01_Link16(msgid, rcid, 0, packingLimit, priority, timeTag, stalenessLimit, rc, reprom_rr, reprom_counter, reprom_request, extrapolation_request, 0, 0, slot_selection_word, stn, 0, l16words);
        return fim;
    }
}
