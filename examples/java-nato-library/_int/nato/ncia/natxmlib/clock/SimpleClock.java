/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.clock;

import java.time.Instant;

/**
 *
 * @author mike
 */
public interface SimpleClock {
    Instant now();
    boolean isRunning();
}
