/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.test;

import _int.nato.ncia.natxmlib.JTIDSDataFrame;
import _int.nato.ncia.natxmlib.clock.SimpleClock;
import _int.nato.ncia.natxmlib.clock.SystemClock;
import fxmlib.fxm.FxM;

/**
 *
 * @author mike
 */
public class RecorderModule {
    protected final static RecorderModule INSTANCE=new RecorderModule();
    
    protected boolean active=false;
    protected SimpleClock clock=SystemClock.getInstance();
    
    private RecorderModule() {
        
    }
    public static RecorderModule getInstance() {
        return INSTANCE;
    }
    public void setActive(boolean active) {
        this.active=active;
    }
    public void setClock(SimpleClock clock) {
        this.clock=clock;
    }
    public boolean isActive() {
        return active;
    }
    protected void record(RecordType rt, byte[] data) {
        
    }
    public void record(JTIDSDataFrame jdf, boolean isTOM) {
        byte[] data=jdf.getBytes();
        record(isTOM?RecordType.TOMFrame:RecordType.TIMFrame,data);
    }
    public void record(FxM fxm, boolean isFOM) {
        fxm.getWords();
    }
    
    public void record(Object obj) {
        
    }
    public void start() {
        
    }
    public void stop() {
        
    }
   
    public enum RecordType {
        TIMFrame,
        TOMFrame,
        FIM,
        FOM
    };
    
}
