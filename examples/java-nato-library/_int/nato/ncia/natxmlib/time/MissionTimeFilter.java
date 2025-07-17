/*
 * Click nbfs://nbhost/SystemFileSystem/Templates/Licenses/license-default.txt to change this license
 * Click nbfs://nbhost/SystemFileSystem/Templates/Classes/Class.java to edit this template
 */
package _int.nato.ncia.natxmlib.time;

import _int.nato.ncia.natxmlib.clock.SimpleClock;
import _int.nato.ncia.natxmlib.clock.SystemClock;
import _int.nato.ncia.natxmlib.fields.TimeStamp;
import _int.nato.ncia.natxmlib.types.TimeStampType;
import java.time.Duration;
import java.time.Instant;
import java.util.LinkedList;

/**
 *
 * @author mike
 */
public class MissionTimeFilter implements SimpleClock {

    protected Instant baseTime = null;
    protected final SimpleClock refClock;

    @Override
    public Instant now() {
        Duration mtd = getCurrentMissionTimeDuration();
        if (mtd != null) {
            return Instant.ofEpochSecond(0).plus(getCurrentMissionTimeDuration());
        } else {
            return null;
        }
    }

    public Instant getBaseTime() {
        return baseTime;
    }

    @Override
    public boolean isRunning() {
        return baseTime != null;
    }

    public MissionTimeFilter() {
        this.refClock = SystemClock.getInstance();
    }

    protected final Object syncObject = new Object();
    protected final LinkedList<Sample> sampleList = new LinkedList<>();

    protected void update(Sample sample) {
        if (sampleList.isEmpty()) {
            baseTime = sample.getBaseTime();
            sampleList.add(sample);
            return;
        }
        Sample minSample = null;
        for (Sample s : sampleList) {
            if (minSample == null) {
                minSample = s;
                continue;
            }
            if (s.getBaseTime().isBefore(minSample.getBaseTime())) {
                minSample = s;
            }
        }
        if (minSample == null) {
            return;
        }
        Duration err = Duration.between(minSample.getBaseTime(), sample.getBaseTime());
        double err_s = err.toNanos() / 1_000_000_000.0;
        if (Math.abs(err_s) < 0.5) {
            if (sampleList.size() >= 60) {
                sampleList.removeFirst();
            }
            sampleList.add(sample);
            if (sample.getBaseTime().isBefore(minSample.getBaseTime())) {
                baseTime = sample.getBaseTime();
            } else {
                baseTime = minSample.getBaseTime();
            }
        } else {
            sampleList.clear();
            sampleList.add(sample);
            baseTime = sample.getBaseTime();
        }
    }

    public void update(Duration mt) {
        Instant now = refClock.now();
        if (now == null) {
            return;
        }
        Sample sample = new Sample(now, mt);
        update(sample);
    }

    public void update(TimeStamp ts) {
        synchronized (syncObject) {
            Instant now = refClock.now();
            if (now == null) {
                return;
            }
            Sample sample = new Sample(now, ts.toDuration());
            update(sample);
        }
    }

    public void setBaseTime(Instant baseTime) {
        this.baseTime = baseTime;
    }
    

    public void reset() {
        synchronized (syncObject) {
            sampleList.clear();
            baseTime = null;
        }
    }

    public TimeStamp getCurrentMissionTime() {
        return TimeStamp.fromDuration(getCurrentMissionTimeDuration());
    }

    public Duration getCurrentMissionTimeDuration() {
        synchronized (syncObject) {
            if (baseTime == null) {
                return null;
            }
            Instant now = SystemClock.getInstance().now();

            if (now == null) {
                return null;
            }
            Duration missionTime = Duration.between(baseTime, now);
            if (missionTime.isNegative()) {
                return null;
            }
            if (missionTime.compareTo(TimeStampType.MAX.toDuration()) > 0) {
                missionTime = missionTime.minus(TimeStampType.MAX.toDuration());
                baseTime = baseTime.plus(TimeStampType.MAX.toDuration());
            }
            return missionTime;
        }
    }

    public static class Sample {

        protected Instant systemTime;
        protected Duration missionTime;
        protected Instant baseTime;

        public Sample(Instant systemTime, Duration missionTime) {
            this.systemTime = systemTime;
            this.missionTime = missionTime;
            this.baseTime = systemTime.minus(missionTime);
        }

        public Instant getSystemTime() {
            return systemTime;
        }

        public Duration getMissionTime() {
            return missionTime;
        }

        public Instant getBaseTime() {
            return baseTime;
        }

    }
}
