/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.messages.tim1;

import _int.nato.ncia.natxmlib.JTIDSDataFrame;
import _int.nato.ncia.natxmlib.messages.AbstractTxM;
import static _int.nato.ncia.natxmlib.messages.NATxM.buildField;
import static _int.nato.ncia.natxmlib.messages.NATxM.createField;
import _int.nato.ncia.natxmlib.types.Field;
import _int.nato.ncia.natxmlib.types.FieldTypes;
import _int.nato.ncia.natxmlib.types.IntegerType;
import java.util.Arrays;
import java.util.LinkedList;
import java.util.List;

/**
 *
 * @author mike
 */
public class NABIM01 extends AbstractTxM {
    protected int[] halfwords;
    
    public NABIM01(List<Field> fields, int[] halfwords) {
        super(1, true, fields);
        this.halfwords=halfwords;
    }

    public boolean isBFI() {
        return ((Field<Boolean>)getField("BLOCK FOLLOWING INDICATOR")).getValue();
    }

    public int getSubBlockId() {
        return ((Field<Integer>)getField("SUB-BLOCK ID")).getValue();
    }
    public static NABIM01 create(boolean bfi, int subBlockId, int[] timHalfwords) {
        List<Field> fields = new LinkedList<>();
        Arrays.copyOf(timHalfwords, subBlockId);
        fields.add(createField("WRAP INDICATOR", 0, 0, FieldTypes.BOOLEAN,0));
        fields.add(createField("BLOCK ID", 0, 1, new IntegerType(5),1));
        fields.add(createField("SUB-BLOCK ID", 8, 1, new IntegerType(4),subBlockId));
        fields.add(createField("ET", 8, 0, FieldTypes.BOOLEAN,0));
        int[] bimHalfwords;
        
        switch(subBlockId) {
            case 1: {
                fields.add(createField("BLOCK FOLLOWING INDICATOR", 8, 15, FieldTypes.BOOLEAN,(bfi?1:0)));
                fields.add(createField("INITIALIZATION BLOCK TYPE", 0, 15, FieldTypes.BOOLEAN,1));
                fields.add(createField("NEW CCCS ORIGIN", 0, 14, FieldTypes.BOOLEAN,0));                
                bimHalfwords=Arrays.copyOfRange(timHalfwords, 0, 16);                
                fields.add(createField("HW2", 0, 16, new IntegerType(16),bimHalfwords[0]));
                fields.add(createField("HW3", 1, 16, new IntegerType(16),bimHalfwords[1]));
                fields.add(createField("HW4", 1, 0, new IntegerType(16),bimHalfwords[2]));
                fields.add(createField("HW5", 2, 16, new IntegerType(16),bimHalfwords[3]));
                fields.add(createField("HW6", 2, 0, new IntegerType(16),bimHalfwords[4]));
                fields.add(createField("HW7", 3, 16, new IntegerType(16),bimHalfwords[5]));
                fields.add(createField("HW8", 3, 0, new IntegerType(16),bimHalfwords[6]));
                fields.add(createField("HW9", 4, 16, new IntegerType(16),bimHalfwords[7]));
                fields.add(createField("HW11", 4, 0, new IntegerType(16),bimHalfwords[8]));
                fields.add(createField("HW10", 5, 16, new IntegerType(16),bimHalfwords[9]));
                fields.add(createField("HW12", 5, 0, new IntegerType(16),bimHalfwords[10]));
                fields.add(createField("HW13", 6, 16, new IntegerType(16),bimHalfwords[11]));
                fields.add(createField("HW14", 6, 0, new IntegerType(16),bimHalfwords[12]));
                fields.add(createField("HW15", 7, 16, new IntegerType(16),bimHalfwords[13]));
                fields.add(createField("HW16", 7, 0, new IntegerType(16),bimHalfwords[14]));
                fields.add(createField("HW17", 8, 16, new IntegerType(16),bimHalfwords[15]));       
            }
            break;
            case 2: {
                bimHalfwords=Arrays.copyOfRange(timHalfwords, 16, 32);
                fields.add(createField("HW20", 0, 16, new IntegerType(16),bimHalfwords[0]));
                fields.add(createField("HW21", 1, 16, new IntegerType(16),bimHalfwords[1]));
                fields.add(createField("HW22", 1, 0, new IntegerType(16),bimHalfwords[2]));
                fields.add(createField("HW23", 2, 16, new IntegerType(16),bimHalfwords[3]));
                fields.add(createField("HW24", 2, 0, new IntegerType(16),bimHalfwords[4]));
                fields.add(createField("HW25", 3, 16, new IntegerType(16),bimHalfwords[5]));
                fields.add(createField("HW26", 3, 0, new IntegerType(16),bimHalfwords[6]));
                fields.add(createField("HW27", 4, 16, new IntegerType(16),bimHalfwords[7]));
                fields.add(createField("HW28", 4, 0, new IntegerType(16),bimHalfwords[8]));
                fields.add(createField("HW29", 5, 16, new IntegerType(16),bimHalfwords[9]));
                fields.add(createField("HW30", 5, 0, new IntegerType(16),bimHalfwords[10]));
                fields.add(createField("HW31", 6, 16, new IntegerType(16),bimHalfwords[11]));
                fields.add(createField("HW32", 6, 0, new IntegerType(16),bimHalfwords[12]));
                fields.add(createField("HW33", 7, 16, new IntegerType(16),bimHalfwords[13]));
                fields.add(createField("HW34", 7, 0, new IntegerType(16),bimHalfwords[14]));
                fields.add(createField("HW35", 8, 16, new IntegerType(16),bimHalfwords[15]));               
            }
            break;
            default:
                throw new IllegalArgumentException();
        }
        return new NABIM01(fields, bimHalfwords);
    }
    public static NABIM01 decode(JTIDSDataFrame frame) {
        List<Field> fields = new LinkedList<>();

        fields.add(buildField(frame, "WRAP INDICATOR", 0, 0, FieldTypes.BOOLEAN));
        Field<Integer> blockId = buildField(frame, "BLOCK ID", 0, 1, new IntegerType(5));
        if(blockId.getValue()!=1) {
            throw new IllegalArgumentException();
        }
        fields.add(blockId);
        
        fields.add(buildField(frame, "ET", 8, 0, FieldTypes.BOOLEAN));
        Field<Integer> subBlockId=buildField(frame, "SUB-BLOCK ID", 8, 1, new IntegerType(4));
        fields.add(subBlockId);
        boolean bfi=false;
        switch (subBlockId.getValue()) {
            case 1:
                fields.add(buildField(frame, "INITIALIZATION BLOCK TYPE", 0, 15, FieldTypes.BOOLEAN)); //1=INIT DATA CHANGE
                fields.add(buildField(frame, "NEW CCCS ORIGIN", 0, 14, FieldTypes.BOOLEAN));
                Field<Boolean> field_bfi = buildField(frame, "BLOCK FOLLOWING INDICATOR", 8, 15, FieldTypes.BOOLEAN);
                fields.add(field_bfi);
                bfi=field_bfi.getValue();
                fields.add(buildField(frame, "HW2", 0, 16, new IntegerType(16)));
                fields.add(buildField(frame, "HW3", 1, 16, new IntegerType(16)));
                fields.add(buildField(frame, "HW4", 1, 0, new IntegerType(16)));
                fields.add(buildField(frame, "HW5", 2, 16, new IntegerType(16)));
                fields.add(buildField(frame, "HW6", 2, 0, new IntegerType(16)));
                fields.add(buildField(frame, "HW7", 3, 16, new IntegerType(16)));
                fields.add(buildField(frame, "HW8", 3, 0, new IntegerType(16)));
                fields.add(buildField(frame, "HW9", 4, 16, new IntegerType(16)));
                fields.add(buildField(frame, "HW10", 4, 0, new IntegerType(16)));
                fields.add(buildField(frame, "HW11", 5, 16, new IntegerType(16)));
                fields.add(buildField(frame, "HW12", 5, 0, new IntegerType(16)));
                fields.add(buildField(frame, "HW13", 6, 16, new IntegerType(16)));
                fields.add(buildField(frame, "HW14", 6, 0, new IntegerType(16)));
                fields.add(buildField(frame, "HW15", 7, 16, new IntegerType(16)));
                fields.add(buildField(frame, "HW16", 7, 0, new IntegerType(16)));
                fields.add(buildField(frame, "HW17", 8, 16, new IntegerType(16)));
                break;
            case 2:
                fields.add(buildField(frame, "HW20", 0, 16, new IntegerType(16)));
                fields.add(buildField(frame, "HW21", 1, 16, new IntegerType(16)));
                fields.add(buildField(frame, "HW22", 1, 0, new IntegerType(16)));
                fields.add(buildField(frame, "HW23", 2, 16, new IntegerType(16)));
                fields.add(buildField(frame, "HW24", 2, 0, new IntegerType(16)));
                fields.add(buildField(frame, "HW25", 3, 16, new IntegerType(16)));
                fields.add(buildField(frame, "HW26", 3, 0, new IntegerType(16)));
                fields.add(buildField(frame, "HW27", 4, 16, new IntegerType(16)));
                fields.add(buildField(frame, "HW28", 4, 0, new IntegerType(16)));
                fields.add(buildField(frame, "HW29", 5, 16, new IntegerType(16)));
                fields.add(buildField(frame, "HW30", 5, 0, new IntegerType(16)));
                fields.add(buildField(frame, "HW31", 6, 16, new IntegerType(16)));
                fields.add(buildField(frame, "HW32", 6, 0, new IntegerType(16)));
                fields.add(buildField(frame, "HW33", 7, 16, new IntegerType(16)));
                fields.add(buildField(frame, "HW34", 7, 0, new IntegerType(16)));
                fields.add(buildField(frame, "HW35", 8, 16, new IntegerType(16)));
                break;
            default:
                throw new IllegalArgumentException();
        }
        int[] halfwords=new int[16];
        int idx=0;
        for(Field f : fields) {
            if(f.getType() instanceof IntegerType) {
                if(f.getType().getLength()==16) {
                    halfwords[idx++]=(Integer)(f.getValue());
                }
            }
        }
        return new NABIM01(fields,halfwords);
    }
}
