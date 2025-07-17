/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.messages.tom4;

import _int.nato.ncia.natxmlib.JTIDSDataFrame;
import _int.nato.ncia.natxmlib.messages.AbstractTxM;
import _int.nato.ncia.natxmlib.messages.NATxM;
import static _int.nato.ncia.natxmlib.messages.NATxM.buildField;
import _int.nato.ncia.natxmlib.types.Field;
import _int.nato.ncia.natxmlib.types.FieldType;
import _int.nato.ncia.natxmlib.types.FieldTypes;
import _int.nato.ncia.natxmlib.types.IntegerType;
import java.util.LinkedList;
import java.util.List;

/**
 *
 * @author mike
 */
public class NATOM04 extends AbstractTxM {
    private NATOM04(List<Field> fields) {
        super(4, false, fields);
    }
    public static NATOM04 create() {
        LinkedList<Field> fields=new LinkedList<>();
        
        fields.add(NATxM.createField("BLOCK ID", 0, 1, new IntegerType(5),4));
        fields.add(NATxM.createField("SYNC STATUS", 1, 7, SyncStatus.TYPE,0));
        fields.add(NATxM.createField("NEW CCCS ORIGIN ACCEPTED", 0, 6, FieldTypes.BOOLEAN,0));
        fields.add(NATxM.createField("TIME", 0, 8, FieldTypes.TIMESTAMP,0));
        fields.add(NATxM.createField("INITIALIZATION COMPLETE", 1, 11, FieldTypes.BOOLEAN,0));
        fields.add(NATxM.createField("INITIALIZATION DATA REQUIRED", 1, 12, FieldTypes.BOOLEAN,0));
        fields.add(NATxM.createField("INITIALIZATION DATA CONFLICT", 1, 13, FieldTypes.BOOLEAN,0));
        fields.add(NATxM.createField("INITIALIZATION DATA ERROR", 1, 14, FieldTypes.BOOLEAN,0));
        fields.add(NATxM.createField("BIT IN PROGRESS", 1, 15, FieldTypes.BOOLEAN,0));
        fields.add(NATxM.createField("NAV INTERFACE FAIL", 1, 16, FieldTypes.BOOLEAN,0));
        fields.add(NATxM.createField("IPF FAIL", 1, 27, FieldTypes.BOOLEAN,0));
        fields.add(NATxM.createField("SDU ALERT", 1, 28, FieldTypes.BOOLEAN,0));
        fields.add(NATxM.createField("TERMINAL FAIL", 1, 29, FieldTypes.BOOLEAN,0));
        fields.add(NATxM.createField("BIT RESULT SUMMARY", 1, 30, BITResultSummary.TYPE,0));
        fields.add(NATxM.createField("INITIALIZATION FROM AOCP", 1, 0, FieldTypes.BOOLEAN,0));
        fields.add(NATxM.createField("USER REFRESH", 1, 1, FieldTypes.BOOLEAN,0));
        
        fields.add(NATxM.createField("STATUS_1", 2, 0, MessageStatusRecord.TYPE,0));
        fields.add(NATxM.createField("STATUS_2", 3, 0, MessageStatusRecord.TYPE,0));
        fields.add(NATxM.createField("STATUS_3", 4, 0, MessageStatusRecord.TYPE,0));
        fields.add(NATxM.createField("STATUS_4", 5, 0, MessageStatusRecord.TYPE,0));
        fields.add(NATxM.createField("STATUS_5", 6, 0, MessageStatusRecord.TYPE,0));
        fields.add(NATxM.createField("STATUS_6", 7, 0, MessageStatusRecord.TYPE,0));        
        
        return new NATOM04(fields);
    }
    public static NATOM04 decode(JTIDSDataFrame frame) {
        LinkedList<Field> fields = new LinkedList<>();
        fields.add(buildField(frame, "WRAP INDICATOR", 0, 0, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "BLOCK ID", 0, 1, new IntegerType(5)));
        fields.add(buildField(frame, "NEW CCCS ORIGIN ACCEPTED", 0, 6, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "NEW CCCS ORIGIN REJECTED", 0, 7, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "TIME", 0, 8, FieldTypes.TIMESTAMP));
        fields.add(buildField(frame, "INITIALIZATION FROM AOCP", 1, 0, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "USER REFRESH", 1, 1, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "(DEGR)", 1, 2, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "(RRF)", 1, 3, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "(CBF)", 1, 4, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "(COR)", 1, 5, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "(SICPBF)", 1, 6, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "SYNC STATUS", 1, 7, SyncStatus.TYPE));
        fields.add(buildField(frame, "(NCSBU)", 1, 9, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "(CMSBU)", 1, 10, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "INITIALIZATION COMPLETE", 1, 11, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "INITIALIZATION DATA REQUIRED", 1, 12, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "INITIALIZATION DATA CONFLICT", 1, 13, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "INITIALIZATION DATA ERROR", 1, 14, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "BIT IN PROGRESS", 1, 15, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "NAV INTERFACE FAIL", 1, 16, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "(SICPDP)", 1, 17, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "(NICPDP)", 1, 18, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "(BATF)", 1, 19, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "(TOL)", 1, 20, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "(TOR)", 1, 21, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "(CMSF)", 1, 23, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "(MSGA)", 1, 24, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "(CCPCPF)", 1, 25, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "RDF DEGRADED PERFORMANCE", 1, 26, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "IPF FAIL", 1, 27, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "SDU ALERT", 1, 28, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "TERMINAL FAIL", 1, 29, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "BIT RESULT SUMMARY", 1, 30, BITResultSummary.TYPE));
        fields.add(buildField(frame, "STATUS_1", 2, 0, MessageStatusRecord.TYPE));
        fields.add(buildField(frame, "STATUS_2", 3, 0, MessageStatusRecord.TYPE));
        fields.add(buildField(frame, "STATUS_3", 4, 0, MessageStatusRecord.TYPE));
        fields.add(buildField(frame, "STATUS_4", 5, 0, MessageStatusRecord.TYPE));
        fields.add(buildField(frame, "STATUS_5", 6, 0, MessageStatusRecord.TYPE));
        fields.add(buildField(frame, "STATUS_6", 7, 0, MessageStatusRecord.TYPE));        
        fields.add(buildField(frame, "ET", 8, 0, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "SUB-BLOCK ID", 8, 1, new IntegerType(4)));
        fields.add(buildField(frame, "CPS COMMAND FAIL (CCF)", 8, 5, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "CPS REPORT FAIL (CRF)", 8, 6, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "RECORDER BUFFER OVERFLOW (RBO)", 8, 7, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "NAF", 8, 8, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "NBF", 8, 9, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "NCF", 8, 10, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "NDF", 8, 11, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "NEF", 8, 12, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "NFF", 8, 13, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "NGF", 8, 14, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "CPS INTERFACE DOWN (CID)", 8, 15, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "IJMS ERROR PERCENTAGE", 8, 16, new IntegerType(7)));
        fields.add(buildField(frame, "IJMS NO TRAFFIC (INT)", 8, 23, FieldTypes.BOOLEAN));
        fields.add(buildField(frame, "JTIDS ERROR PERCENTAGE", 8, 24, new IntegerType(7)));
        fields.add(buildField(frame, "JTIDS NO TRAFFIC (JNT)", 8, 31, FieldTypes.BOOLEAN));
        return new NATOM04(fields);
    }
    public enum BITResultSummary {
        NO_STATMENT,
        TEST_GO,
        TEST_FAIL,
        NOT_USED;
        public final static FieldType<BITResultSummary> TYPE = new FieldType<>() {
            @Override
            public int getLength() {
               return 2;
            }

            @Override
            public BITResultSummary decode(long code) {
                return BITResultSummary.values()[(int)code];
            }

            @Override
            public long encode(BITResultSummary value) {
                return value.ordinal();
            }            
        };
    }
    public enum SyncStatus {
        NET_ENTRY_NOT_IN_PROGRESS,
        COARSE_SYNC_IN_PROGRESS,
        COARSE_SYNC_ACHIEVED,
        FINE_SYNC_ACHIEVED;
        public final static FieldType<SyncStatus> TYPE = new FieldType<>() {
            @Override
            public int getLength() {
               return 2;
            }

            @Override
            public SyncStatus decode(long code) {
                return SyncStatus.values()[(int)code];
            }

            @Override
            public long encode(SyncStatus value) {
                return value.ordinal();
            }            
        };
                
    }

    
}
