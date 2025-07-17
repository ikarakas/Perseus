package _int.nato.ncia.natxmlib.messages.tom3;

import _int.nato.ncia.natxmlib.JTIDSDataFrame;
import _int.nato.ncia.natxmlib.fields.TimeStamp;
import _int.nato.ncia.natxmlib.messages.NATOM;
import _int.nato.ncia.natxmlib.messages.common.JWordData;
import _int.nato.ncia.natxmlib.messages.common.SubgroupData;
import _int.nato.ncia.natxmlib.types.Field;
import java.util.Arrays;
import java.util.LinkedList;

/**
 *
 * @author mike
 */
public class NATOM03 extends NATOM {

    private NATOM03() {
    }
    protected NABOM03[] boms;
    protected SubgroupData[] subGroupData;

    public NATOM03(NABOM03[] boms, SubgroupData[] subGroupData) {
        this.boms = boms;
        this.subGroupData = subGroupData;
    }
    
    public static NATOM03 decode(NABOM03[] boms) {
        
        LinkedList<SubgroupData> sgdata = new LinkedList<>();
        for (NABOM03 bom : boms) {
            if (bom.data != null) {
                for (SubgroupData sgd : bom.data) {
                    if (sgdata.size() < boms[0].getLength()) {
                        sgdata.add(sgd);
                    }
                }
            }
        }
        NATOM03 tom = new NATOM03();
        tom.subGroupData = sgdata.toArray(new SubgroupData[0]);
        if (tom.subGroupData.length != boms[0].getLength()) {
            throw new IllegalArgumentException("subgroup length mismatch");
        }
        tom.boms=boms;
        return tom;
    }

    public SubgroupData[] getData() {
        return subGroupData;
    }
    public int getSTN() {
        return boms[0].getSTN();
    }
    public int getNPG() {
        return boms[0].getNPG();
    }
    @Override
    public int getBlockId() {
        return 3;
    }

    @Override
    public Iterable<Field> fields() {
        return boms[0].fields();
    }

    @Override
    public JTIDSDataFrame[] encode() {
        JTIDSDataFrame[] result = new JTIDSDataFrame[boms.length];
        for(int i=0;i<result.length;i++) {
            result[i]=boms[i].encode()[0];
        }
        return result;
    }
    public static NATOM03 create(int stn, int npg, TimeStamp time, SubgroupData[] sgs) {
        int numBoms;
        if(sgs.length>2) {
            int l2=sgs.length-2;
            numBoms=1+l2/3;
            if((l2 % 3 )!=0) {
                numBoms++;
            }
        }else{
            numBoms=1;
        }
        NABOM03[] boms=new NABOM03[numBoms];
        SubgroupData[] xsgs=new SubgroupData[2+(numBoms-1)*3];
        for(int i=0;i<xsgs.length;i++) {
            if(i<sgs.length) {
                xsgs[i]=sgs[i];
            }else{
                xsgs[i]=new JWordData();
            }
        }
        for(int i=0;i<boms.length;i++) {
            SubgroupData[] bsd=(i==0)?Arrays.copyOfRange(xsgs, 0, 2):Arrays.copyOfRange(xsgs, i*3-1, i*3+2);
            boms[i]=new NABOM03(i+1, bsd);
        }
        boms[0].getField("STN").setCode(stn);
        boms[0].getField("NPG").setCode(npg);
        boms[0].getField("TIME").setValue(time);
        boms[0].getField("LENGTH").setValue(sgs.length);
        boms[0].getField("SUBBLOCK COUNT").setValue(boms.length);
        return new NATOM03(boms,sgs);
    }
}
