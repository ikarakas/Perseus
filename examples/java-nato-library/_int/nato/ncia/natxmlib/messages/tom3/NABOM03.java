/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.messages.tom3;

import _int.nato.ncia.natxmlib.HICDataFrame;
import _int.nato.ncia.natxmlib.JTIDSDataFrame;
import _int.nato.ncia.natxmlib.fields.TimeStamp;
import _int.nato.ncia.natxmlib.messages.AbstractTxM;
import static _int.nato.ncia.natxmlib.messages.NATxM.buildField;
import _int.nato.ncia.natxmlib.messages.common.SubgroupData;
import _int.nato.ncia.natxmlib.types.Field;
import _int.nato.ncia.natxmlib.types.FieldTypes;
import _int.nato.ncia.natxmlib.types.IntegerType;
import java.util.Collections;
import java.util.LinkedList;
import java.util.List;

/**
 *
 * @author mike
 */
public class NABOM03 extends AbstractTxM {    
    protected SubgroupData[] data;

    public NABOM03(List<Field> fields) {
        super(3, false, fields);
    }
    public NABOM03(int subBlockId, SubgroupData[] data) {
        super(3, false, Collections.EMPTY_LIST);
        addField("WRAP INDICATOR", 0, 0, FieldTypes.BOOLEAN,0);
        addField("BLOCK ID", 0, 1, new IntegerType(5),3);
        addField("ET", 8, 0, FieldTypes.BOOLEAN,0);
        addField("SUB-BLOCK ID", 8, 1, new IntegerType(4),subBlockId);

        switch(subBlockId) {
            case 1:
            {
                addField("TIME", 0, 8, FieldTypes.TIMESTAMP);
                addField("STN", 1, 0, new IntegerType(15));
                addField("RC LOOPBACK ID", 2, 0, new IntegerType(12));                
                addField("NPG", 2, 16, new IntegerType(9));                
                addField("LENGTH", 1, 16, new IntegerType(5));
                addField("SUBBLOCK COUNT", 1, 21, new IntegerType(3));
                addField("TYPE", 1, 28, new IntegerType(4));
            }            
            break;
            
            case 2:
            case 3:
            case 4:
            case 5:
            case 6:
            case 7: {
                
            }
            break;
            default:
                throw new IllegalArgumentException();
        }
        this.data=data;
    }

    @Override
    public boolean isTIM() {
        return false;
    }

    @Override
    public int getBlockId() {
        return 3;
    }

    public int getLength() {
        return ((Field<Integer>)map.get("LENGTH")).getValue();
    }

    public int getSubBlockCount() {
        return ((Field<Integer>)map.get("SUBBLOCK COUNT")).getValue();
    }

    public int getSubBlockId() {
        return ((Field<Integer>)map.get("SUB-BLOCK ID")).getValue();
    }

    public int getSTN() {
        return ((Field<Integer>)map.get("STN")).getValue();
    }
    public int getNPG() {
        return ((Field<Integer>)map.get("NPG")).getValue();
    }
    public int getLoopbackId() {
        return ((Field<Integer>)map.get("RC LOOPBACK ID")).getValue();
    }
    @Override
    public String getName() {
        return "BOM3-"+getSubBlockId();
    }
    public TimeStamp getTime() {
        return ((Field<TimeStamp>)map.get("TIME")).getValue();
        
    }
    public static NABOM03 decode(JTIDSDataFrame frame) {
        LinkedList<Field> fields = new LinkedList<>();
        fields.add(buildField(frame, "WRAP INDICATOR", 0, 0, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "BLOCK ID", 0, 1, new IntegerType(5)));
        fields.add(buildField(frame, "ET", 8, 0, FieldTypes.BOOLEAN));
        Field<Integer> subBlockId = buildField(frame, "SUB-BLOCK ID", 8, 1, new IntegerType(4));
        fields.add(subBlockId);
        SubgroupData[] data=null;
        switch (subBlockId.getValue()) {
            case 1:
                fields.add(buildField(frame, "TIME", 0, 8, FieldTypes.TIMESTAMP));
                fields.add(buildField(frame, "TYPE", 1, 28, new IntegerType(4)));
                fields.add(buildField(frame, "STN", 1, 0, new IntegerType(15)));
                Field<Integer> length = buildField(frame, "LENGTH", 1, 16, new IntegerType(5));
                fields.add(length);
                Field<Integer> subBlockCount = buildField(frame, "SUBBLOCK COUNT", 1, 21, new IntegerType(3));
                fields.add(subBlockCount);
                fields.add(buildField(frame, "TYPE", 1, 28, new IntegerType(4)));
                data = new SubgroupData[]{SubgroupData.decode(frame, 3), SubgroupData.decode(frame, 6)};
                break;
            case 2:
            case 3:
            case 4:
            case 5:
            case 6:
            case 7:
                data = new SubgroupData[]{SubgroupData.decode(frame, 0), SubgroupData.decode(frame, 3), SubgroupData.decode(frame, 6)};
                break;
            default:
                throw new IllegalArgumentException();

            
        }
        NABOM03 bom = new NABOM03(fields);
        bom.data=data;
        return bom;
    }

    @Override
    public JTIDSDataFrame[] encode() {
        HICDataFrame frame = HICDataFrame.create();
        switch(getSubBlockId()) {
            case 1:
                data[0].put(frame, 3);
                data[1].put(frame, 6);
                break;
            case 2:
            case 3:
            case 4:
            case 5:
            case 6:
            case 7:
                data[0].put(frame, 0);
                data[1].put(frame, 3);
                data[2].put(frame, 6);
                break;
            default:
                throw new IllegalArgumentException();                        
        }
        for (Field f : map.values()) {
            frame.setCode(f.getOffset() / 32, f.getOffset() % 32, f.getLength(), (int) f.getCode());
        }
        
        return new JTIDSDataFrame[]{frame};
    }
    
}
