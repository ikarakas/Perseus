/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.messages.tim3;

import _int.nato.ncia.natxmlib.messages.common.SubgroupData;
import _int.nato.ncia.natxmlib.JTIDSDataFrame;
import _int.nato.ncia.natxmlib.messages.NATxM;
import static _int.nato.ncia.natxmlib.messages.NATxM.buildField;
import _int.nato.ncia.natxmlib.types.Field;
import _int.nato.ncia.natxmlib.types.FieldTypes;
import _int.nato.ncia.natxmlib.types.GenericMessageField;
import _int.nato.ncia.natxmlib.types.IntegerType;
import _int.nato.ncia.natxmlib.types.PackingLimit;
import java.util.LinkedList;
import java.util.List;
import java.util.Map;
import java.util.TreeMap;

/**
 *
 * @author mike
 */
public class NABIM03 implements NATxM {

    protected final List<Field> fields;
    protected SubgroupData[] data;
    protected Map<String, Field> fieldMap=new TreeMap<>();
    
    public NABIM03(List<Field> fields) {
        this.fields = fields;
        for(Field f : fields) {
            if(f instanceof GenericMessageField) {
                fieldMap.put(((GenericMessageField) f).getName(),f);
            }
        }
    }
    
    public int getSubBlockId() {
        return ((Field<Integer>)fieldMap.get("SUB-BLOCK ID")).getValue();
    }

    public int getSubBlockCount() {
        return ((Field<Integer>)fieldMap.get("SUBBLOCK COUNT")).getValue();
    }

    public int getLength() {
        return ((Field<Integer>)fieldMap.get("LENGTH")).getValue();
    }

    public SubgroupData[] getData() {
        return data;
    }
    public Field getField(String name) {
        return fieldMap.get(name);
    }
    public static NABIM03 decode(JTIDSDataFrame frame) {
        List<Field> fields = new LinkedList<>();

        fields.add(buildField(frame, "WRAP INDICATOR", 0, 0, FieldTypes.BOOLEAN));
        Field<Integer> blockId = buildField(frame, "BLOCK ID", 0, 1, new IntegerType(5));
        if(blockId.getValue()!=3) {
            throw new IllegalArgumentException("Expected TIM03 received TIM"+String.format("%02d",blockId.getValue())+" instead!");
        }
        fields.add(blockId);
        
        fields.add(buildField(frame, "ET", 8, 0, FieldTypes.BOOLEAN));
        Field<Integer> subBlockId = buildField(frame, "SUB-BLOCK ID", 8, 1, new IntegerType(4));
        fields.add(subBlockId);
        
        SubgroupData[] data;
        switch (subBlockId.getValue()) {
            case 1:
                fields.add(buildField(frame, "TIME", 0, 8, FieldTypes.TIMESTAMP));
                fields.add(buildField(frame, "RECURRENCY RATE", 1, 5, new IntegerType(3)));
                fields.add(buildField(frame, "PACKING LIMIT", 1, 0, PackingLimit.TYPE));
                fields.add(buildField(frame, "NUMBER OF REPEATED TRANSMISSIONS", 1, 3, new IntegerType(2)));
                fields.add(buildField(frame, "EXTRAPOLATION REQUEST", 1, 15, FieldTypes.BOOLEAN));
                fields.add(buildField(frame, "LENGTH", 1, 16, new IntegerType(5)));
                fields.add(buildField(frame, "SUBBLOCK COUNT", 1, 21, new IntegerType(3)));
                fields.add(buildField(frame, "NPG", 2, 0, new IntegerType(9)));
                fields.add(buildField(frame, "PRIORITY", 2, 16, new IntegerType(4)));
                fields.add(buildField(frame, "STALENESS LIMIT", 3, 0, new IntegerType(5)));
                fields.add(buildField(frame, "REPROMULGATION COUNTER", 4, 0, new IntegerType(4)));
                fields.add(buildField(frame, "REPROMULGATION REQUIRED", 4, 15, FieldTypes.BOOLEAN));
                fields.add(buildField(frame, "LOOPBACK ID", 4, 16, new IntegerType(12)));                
                fields.add(buildField(frame, "RECEIPT COMPLIANCE", 4, 31, FieldTypes.BOOLEAN));
                fields.add(buildField(frame, "STN", 5, 0, new IntegerType(15)));
                
                data = new SubgroupData[]{SubgroupData.decode(frame, 6)};
                break;
            case 2:
            case 3:
            case 4:
            case 5:
            case 6:
            case 7:
                data = new SubgroupData[]{SubgroupData.decode(frame, 0),SubgroupData.decode(frame, 3),SubgroupData.decode(frame, 6)};
                break;
            default:
                throw new IllegalArgumentException();
        }
        NABIM03 bim = new NABIM03(fields);
        bim.data=data;
        return bim;
    }

    @Override
    public boolean isTIM() {
        return true;
    }

    @Override
    public int getBlockId() {
        return 3;
    }

    @Override
    public Iterable<Field> fields() {
        return fields;
    }

    @Override
    public String getName() {
        return "TIM03-" + getSubBlockId();
    }


}
