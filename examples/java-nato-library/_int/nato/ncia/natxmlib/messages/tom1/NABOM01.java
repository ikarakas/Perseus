/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.messages.tom1;

import _int.nato.ncia.natxmlib.HICDataFrame;
import _int.nato.ncia.natxmlib.JTIDSDataFrame;
import _int.nato.ncia.natxmlib.messages.NATxM;
import static _int.nato.ncia.natxmlib.messages.NATxM.buildField;
import static _int.nato.ncia.natxmlib.messages.NATxM.createField;
import _int.nato.ncia.natxmlib.types.Field;
import _int.nato.ncia.natxmlib.types.FieldTypes;
import _int.nato.ncia.natxmlib.types.IntegerType;
import java.util.LinkedList;
import java.util.List;

/**
 *
 * @author mike
 */
public class NABOM01 implements NATxM {

    protected final List<Field> fields;
    protected int[] halfwords;
    protected boolean bfi;
    protected int subBlockId;

    public NABOM01(List<Field> fields, int[] halfwords) {
        this.fields = fields;
        this.halfwords = halfwords;
    }
    
    public boolean isBFI() {
        return bfi;
    }

    public int getSubBlockId() {
        return subBlockId;
    }
    public NABOM01(int subBlockId, boolean bfi, int[] datahalfwords) {
        halfwords=new int[16];
        for(int i=0;i<halfwords.length;i++) {
            if(i<datahalfwords.length) {
                halfwords[i]=datahalfwords[i];
            }else{
                halfwords[i]=0;
            }
        }
        fields=new LinkedList<>();
        fields.add(createField("WRAP INDICATOR", 0, 0, FieldTypes.BOOLEAN,0));
        fields.add(createField("BLOCK ID", 0, 1, new IntegerType(5),1));
        fields.add(createField("SUB-BLOCK ID", 8, 1, new IntegerType(4),subBlockId));
        if(subBlockId==1) {
            fields.add(createField("BLOCK FOLLOWING INDICATOR", 8, 15, FieldTypes.BOOLEAN,bfi?1:0));    
        }
        int wo=(subBlockId==1)?2:20;
        for(int i=0;i<halfwords.length;i++) {
             int widx=((i+1)/2);
             int bidx=(i==0)?16:(((i%2)==0)?0:16);
             Field<Integer> fieldHW = createField("HW"+(wo+i), widx, bidx, new IntegerType(16),halfwords[i]);
             fields.add(fieldHW);
        }        
    }
    @Override
    public JTIDSDataFrame[] encode() {
        HICDataFrame frame=HICDataFrame.create();
        for(Field f : fields) {
            frame.setCode(f.getOffset()/32, f.getOffset()%32, f.getLength(), (int)f.getCode());
        }
        return new JTIDSDataFrame[]{frame};
    }

    public static NABOM01 decode(JTIDSDataFrame frame) {
        List<Field> fields = new LinkedList<>();

        fields.add(buildField(frame, "WRAP INDICATOR", 0, 0, FieldTypes.BOOLEAN));
        Field<Integer> blockId = buildField(frame, "BLOCK ID", 0, 1, new IntegerType(5));
        if (blockId.getValue() != 1) {
            throw new IllegalArgumentException();
        }
        fields.add(blockId);

        fields.add(buildField(frame, "ET", 8, 0, FieldTypes.BOOLEAN));
        Field<Integer> subBlockId = buildField(frame, "SUB-BLOCK ID", 8, 1, new IntegerType(4));
        fields.add(subBlockId);
        boolean bfi = false;
        switch (subBlockId.getValue()) {
            case 1:
                Field<Boolean> field_bfi = buildField(frame, "BLOCK FOLLOWING INDICATOR", 8, 15, FieldTypes.BOOLEAN);
                fields.add(field_bfi);
                bfi = field_bfi.getValue();
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
        int[] halfwords = new int[16];
        int idx = 0;
        for (Field f : fields) {
            if (f.getType() instanceof IntegerType) {
                if (f.getType().getLength() == 16) {
                    halfwords[idx++] = (Integer) (f.getValue());
                }
            }
        }
        NABOM01 bim = new NABOM01(fields, halfwords);
        bim.bfi = bfi;
        bim.subBlockId = subBlockId.getValue();
        return bim;
    }

    @Override
    public boolean isTIM() {
        return false;
    }

    @Override
    public int getBlockId() {
        return 1;
    }

    @Override
    public Iterable<Field> fields() {
        return fields;
    }

    @Override
    public String getName() {
        return "TOM1";
    }

  
}
