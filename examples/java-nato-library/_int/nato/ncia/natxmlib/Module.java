/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Interface.java to edit this template
 */
package _int.nato.ncia.natxmlib;

/**
 *
 * @author mike
 */
public interface Module {
    boolean isActive();
    Status getStatus();
    default String getStatusText() {
        return getStatus().name();
    }
    public static enum Status {
        CREATED,
        INITIALIZING,
        RUNNING,
        FAILURE;
    }
    
}
