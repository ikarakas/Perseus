package _int.nato.ncia.natxmlib.messages.tim3;

import _int.nato.ncia.natxmlib.messages.NATIM;
import _int.nato.ncia.natxmlib.fields.TimeStamp;
import _int.nato.ncia.natxmlib.messages.common.SubgroupData;
import _int.nato.ncia.natxmlib.types.Field;
import _int.nato.ncia.natxmlib.types.PackingLimit;
import java.util.Collections;
import java.util.LinkedList;

/**
 *
 * @author mike
 */
public class NATIM03 extends NATIM {

    protected final NABIM03[] bims;
    protected final SubgroupData[] data;

    public NATIM03(NABIM03[] bims, SubgroupData[] data) {
        this.bims = bims;
        this.data = data;
    }
    
   
    public int getSTN() {
        return ((Field<Integer>)bims[0].getField("STN")).getValue();
    }
    public int getNPG() {
        return ((Field<Integer>)bims[0].getField("NPG")).getValue();
    }
    public PackingLimit getPackingLimit() {
        return ((Field<PackingLimit>)bims[0].getField("PACKING LIMIT")).getValue();
    }
    public int getPriority() {
        return ((Field<Integer>)bims[0].getField("PRIORITY")).getValue();
    }
    public TimeStamp getTime() {
        return ((Field<TimeStamp>)bims[0].getField("TIME")).getValue();
    }
    public int getStalenessLimit() {
        return ((Field<Integer>)bims[0].getField("STALENESS LIMIT")).getValue();        
    }
    public int getRepeatedTransmissionRecurrencyRate() {
        return ((Field<Integer>)bims[0].getField("RECURRENCY RATE")).getValue();        
    }
    public int getRepromRecurrencyCount() {
        return ((Field<Integer>)bims[0].getField("NUMBER OF REPEATED TRANSMISSIONS")).getValue();        
    }
    public boolean getRepromRequired() {
        return ((Field<Boolean>)bims[0].getField("REPROMULGATION REQUIRED")).getValue();        
    }
    public int getRepromCount() {
        return ((Field<Integer>)bims[0].getField("REPROMULGATION COUNTER")).getValue();        
    }    
    public boolean getExtrapolationRequest() {
        return ((Field<Boolean>)bims[0].getField("EXTRAPOLATION REQUEST")).getValue();        
    }
    public boolean getReceiptCompliance() {
        return ((Field<Boolean>)bims[0].getField("RECEIPT COMPLIANCE")).getValue();        
    }    
    public int getLoopbackId() {
        return ((Field<Integer>)bims[0].getField("LOOPBACK ID")).getValue();        
    }    
    public int getNumberOfRepeatedTransmissions() {
        return ((Field<Integer>)bims[0].getField("NUMBER OF REPEATED TRANSMISSIONS")).getValue();                
    }
    public SubgroupData[] getData() {
        return data;
    }
        
    public static NATIM03 decode(NABIM03[] bims) {
        LinkedList<SubgroupData> sgdata = new LinkedList<>();
        for(NABIM03 bim : bims) {
            if(bim.data!=null) {
                for(SubgroupData sgd : bim.data) {
                    if(sgdata.size()<bims[0].getLength()) {
                        sgdata.add(sgd);
                    }
                }
            }
        }
       if(sgdata.size()!=bims[0].getLength()) {
           throw new IllegalArgumentException("subgroup length mismatch");
       }
       NATIM03 tim = new NATIM03(bims,sgdata.toArray(new SubgroupData[0]));
       return tim;
    }

    @Override
    public int getBlockId() {
        return 3;
    }

    @Override
    public Iterable<Field> fields() {
        return Collections.EMPTY_LIST;
    }

}
