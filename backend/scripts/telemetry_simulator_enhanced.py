"""
Enhanced telemetry simulator with UI controls and realistic EV charging patterns
"""
import asyncio
import random
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import redis
import httpx
import os
import sys
import logging
from dataclasses import dataclass
from enum import Enum

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ChargerStatus(Enum):
    AVAILABLE = "available"
    IN_USE = "in_use"
    MAINTENANCE = "maintenance"
    OFFLINE = "offline"
    FAULT = "fault"

class ChargingProfile(Enum):
    SLOW_AC = "slow_ac"        # 3.7kW - Home charging
    FAST_AC = "fast_ac"        # 7-22kW - Public AC
    DC_FAST = "dc_fast"        # 50-150kW - Highway charging
    ULTRA_FAST = "ultra_fast"  # 250kW+ - Tesla Supercharger

@dataclass
class TelemetryPoint:
    timestamp: datetime
    power_output_kw: float
    voltage_v: float
    current_a: float
    temperature_c: float
    energy_delivered_kwh: float
    session_duration_minutes: int
    status: ChargerStatus
    error_code: Optional[str] = None

class EVChargingSimulator:
    """Simulates realistic EV charging curves and behavior"""
    
    def __init__(self, charger_id: int, max_power_kw: float, profile: ChargingProfile):
        self.charger_id = charger_id
        self.max_power_kw = max_power_kw
        self.profile = profile
        self.session_start = None
        self.session_id = None
        self.target_energy_kwh = 0
        self.delivered_energy_kwh = 0
        self.base_temperature = 25.0
        self.current_status = ChargerStatus.AVAILABLE
        
        # Charging curve parameters
        self.charging_phases = {
            ChargingProfile.SLOW_AC: {
                'constant_power_until': 80,  # % battery
                'taper_start': 80,
                'taper_rate': 0.02,  # Power reduction per % above taper_start
                'efficiency': 0.90
            },
            ChargingProfile.FAST_AC: {
                'constant_power_until': 85,
                'taper_start': 85,
                'taper_rate': 0.03,
                'efficiency': 0.88
            },
            ChargingProfile.DC_FAST: {
                'constant_power_until': 80,
                'taper_start': 70,
                'taper_rate': 0.04,
                'efficiency': 0.85
            },
            ChargingProfile.ULTRA_FAST: {
                'constant_power_until': 70,
                'taper_start': 50,
                'taper_rate': 0.06,
                'efficiency': 0.82
            }
        }
    
    def start_charging_session(self, target_energy_kwh: float = None):
        """Start a new charging session"""
        self.session_start = datetime.utcnow()
        self.session_id = f"session_{self.charger_id}_{int(time.time())}"
        self.target_energy_kwh = target_energy_kwh or random.uniform(20, 80)
        self.delivered_energy_kwh = 0
        self.current_status = ChargerStatus.IN_USE
        
        logger.info(f"🔌 Charger {self.charger_id} started session {self.session_id}, target: {self.target_energy_kwh:.1f} kWh")
    
    def stop_charging_session(self):
        """Stop the current charging session"""
        if self.session_id:
            logger.info(f"🔋 Charger {self.charger_id} completed session {self.session_id}, delivered: {self.delivered_energy_kwh:.1f} kWh")
        
        self.session_start = None
        self.session_id = None
        self.target_energy_kwh = 0
        self.delivered_energy_kwh = 0
        self.current_status = ChargerStatus.AVAILABLE
    
    def get_charging_power(self, session_duration_minutes: int) -> float:
        """Calculate realistic charging power based on charging curve"""
        if self.current_status != ChargerStatus.IN_USE:
            return 0.0
        
        # Calculate battery state of charge (simplified)
        progress_ratio = min(self.delivered_energy_kwh / max(self.target_energy_kwh, 1), 1.0)
        battery_soc = progress_ratio * 100  # Convert to percentage
        
        # Get charging curve parameters
        curve = self.charging_phases[self.profile]
        
        # Constant power phase
        if battery_soc <= curve['taper_start']:
            base_power = self.max_power_kw
        else:
            # Taper phase - reduce power as battery fills
            taper_amount = (battery_soc - curve['taper_start']) * curve['taper_rate']
            base_power = self.max_power_kw * (1 - taper_amount)
        
        # Add some realistic variation
        variation = random.uniform(-0.05, 0.05)  # ±5% variation
        power = base_power * (1 + variation)
        
        # Environmental factors (temperature, grid voltage, etc.)
        if session_duration_minutes > 60:  # Heat buildup after 1 hour
            heat_reduction = min(0.1, (session_duration_minutes - 60) * 0.001)
            power *= (1 - heat_reduction)
        
        return max(0, min(power, self.max_power_kw))
    
    def get_telemetry(self) -> TelemetryPoint:
        """Generate current telemetry data"""
        now = datetime.utcnow()
        
        if self.current_status == ChargerStatus.IN_USE and self.session_start:
            session_duration = int((now - self.session_start).total_seconds() / 60)
            current_power = self.get_charging_power(session_duration)
            
            # Calculate energy delivered (kWh = kW * hours)
            time_delta = 1/60  # 1 minute in hours
            energy_delta = current_power * time_delta * self.charging_phases[self.profile]['efficiency']
            self.delivered_energy_kwh += energy_delta
            
            # Calculate voltage and current based on power
            if self.profile in [ChargingProfile.SLOW_AC, ChargingProfile.FAST_AC]:
                voltage = random.uniform(220, 240)  # AC voltage
            else:
                voltage = random.uniform(350, 450)  # DC voltage
            
            current = (current_power * 1000) / voltage if voltage > 0 else 0
            
            # Temperature increases with power and time
            temp_increase = (current_power / self.max_power_kw) * 25 + (session_duration / 120) * 10
            temperature = self.base_temperature + temp_increase + random.uniform(-2, 2)
            
            # Check if session should end
            if self.delivered_energy_kwh >= self.target_energy_kwh or session_duration > 300:  # 5 hours max
                self.stop_charging_session()
                
        else:
            session_duration = 0
            current_power = 0
            voltage = random.uniform(220, 240)
            current = 0
            temperature = self.base_temperature + random.uniform(-3, 3)
        
        return TelemetryPoint(
            timestamp=now,
            power_output_kw=round(current_power, 2),
            voltage_v=round(voltage, 1),
            current_a=round(current, 2),
            temperature_c=round(temperature, 1),
            energy_delivered_kwh=round(self.delivered_energy_kwh, 3),
            session_duration_minutes=session_duration,
            status=self.current_status
        )

class TelemetryManager:
    """Manages multiple charger simulators"""
    
    def __init__(self):
        self.simulators: Dict[int, EVChargingSimulator] = {}
        self.redis_client = None
        self.http_client = httpx.AsyncClient(timeout=30.0)
        self.running = False
        
        # Initialize Redis connection
        try:
            self.redis_client = redis.from_url(settings.REDIS_URL)
            self.redis_client.ping()
            logger.info("✅ Connected to Redis")
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
    
    def initialize_simulators(self):
        """Initialize charger simulators with realistic configurations"""
        # Sample charger configurations
        charger_configs = [
            (1, 120, ChargingProfile.DC_FAST),      # DC Fast charger
            (2, 22, ChargingProfile.FAST_AC),       # AC Fast charger  
            (3, 150, ChargingProfile.DC_FAST),      # High-power DC
            (4, 7, ChargingProfile.FAST_AC),        # Standard AC
            (5, 250, ChargingProfile.ULTRA_FAST),   # Tesla Supercharger
        ]
        
        for charger_id, max_power, profile in charger_configs:
            self.simulators[charger_id] = EVChargingSimulator(charger_id, max_power, profile)
            logger.info(f"📊 Initialized simulator for charger {charger_id} ({max_power}kW, {profile.value})")
    
    async def simulate_random_sessions(self):
        """Randomly start and stop charging sessions"""
        while self.running:
            try:
                for charger_id, sim in self.simulators.items():
                    # Random chance to start/stop sessions
                    if sim.current_status == ChargerStatus.AVAILABLE:
                        if random.random() < 0.002:  # 0.2% chance per iteration
                            target_energy = random.uniform(15, 75)  # Realistic charging amounts
                            sim.start_charging_session(target_energy)
                    
                    elif sim.current_status == ChargerStatus.IN_USE:
                        # Small chance to stop session early
                        if random.random() < 0.001:
                            sim.stop_charging_session()
                    
                    # Random faults and maintenance
                    if random.random() < 0.0001:  # Very low chance
                        if sim.current_status == ChargerStatus.AVAILABLE:
                            sim.current_status = random.choice([ChargerStatus.MAINTENANCE, ChargerStatus.FAULT])
                            logger.warning(f"⚠️ Charger {charger_id} status changed to {sim.current_status}")
                    
                    elif sim.current_status in [ChargerStatus.MAINTENANCE, ChargerStatus.FAULT]:
                        if random.random() < 0.01:  # 1% chance to recover
                            sim.current_status = ChargerStatus.AVAILABLE
                            logger.info(f"✅ Charger {charger_id} back online")
                
                await asyncio.sleep(5)  # Check every 5 seconds
                
            except Exception as e:
                logger.error(f"Error in session simulation: {e}")
                await asyncio.sleep(10)
    
    async def publish_telemetry(self):
        """Publish telemetry data to Redis channels"""
        while self.running:
            try:
                for charger_id, sim in self.simulators.items():
                    telemetry = sim.get_telemetry()
                    
                    # Convert to message format
                    message = {
                        "type": "telemetry_update",
                        "charger_id": charger_id,
                        "timestamp": telemetry.timestamp.isoformat(),
                        "status": telemetry.status.value,
                        "power_output_kw": telemetry.power_output_kw,
                        "voltage_v": telemetry.voltage_v,
                        "current_a": telemetry.current_a,
                        "temperature_c": telemetry.temperature_c,
                        "energy_delivered_kwh": telemetry.energy_delivered_kwh,
                        "session_duration_minutes": telemetry.session_duration_minutes,
                        "session_id": sim.session_id,
                        "connectivity_status": "online",
                        "signal_strength": random.randint(70, 100),
                        "firmware_version": "1.2.3"
                    }
                    
                    # Publish to Redis channel
                    if self.redis_client:
                        try:
                            channel = f"charger_telemetry_{charger_id}"
                            self.redis_client.publish(channel, json.dumps(message))
                            
                            # Also publish to general telemetry channel
                            self.redis_client.publish("charger_telemetry", json.dumps(message))
                            
                        except Exception as e:
                            logger.error(f"Failed to publish telemetry for charger {charger_id}: {e}")
                    
                    # Log significant events
                    if telemetry.power_output_kw > 0 and random.random() < 0.1:
                        logger.info(
                            f"📊 Charger {charger_id}: {telemetry.power_output_kw:.1f}kW, "
                            f"{telemetry.energy_delivered_kwh:.1f}kWh delivered, "
                            f"{telemetry.session_duration_minutes}min elapsed"
                        )
                
                await asyncio.sleep(settings.TELEMETRY_UPDATE_INTERVAL)
                
            except Exception as e:
                logger.error(f"Error publishing telemetry: {e}")
                await asyncio.sleep(5)
    
    def manual_control(self, charger_id: int, action: str, **kwargs):
        """Manual control for testing"""
        if charger_id not in self.simulators:
            logger.error(f"Charger {charger_id} not found")
            return
        
        sim = self.simulators[charger_id]
        
        if action == "start_session":
            target_energy = kwargs.get("target_energy", random.uniform(20, 60))
            sim.start_charging_session(target_energy)
            logger.info(f"🎮 Manually started session on charger {charger_id}")
            
        elif action == "stop_session":
            sim.stop_charging_session()
            logger.info(f"🎮 Manually stopped session on charger {charger_id}")
            
        elif action == "set_fault":
            sim.current_status = ChargerStatus.FAULT
            logger.info(f"🎮 Set charger {charger_id} to fault status")
            
        elif action == "set_maintenance":
            sim.current_status = ChargerStatus.MAINTENANCE
            logger.info(f"🎮 Set charger {charger_id} to maintenance status")
            
        elif action == "set_available":
            sim.current_status = ChargerStatus.AVAILABLE
            sim.stop_charging_session()
            logger.info(f"🎮 Set charger {charger_id} to available status")
    
    async def run(self):
        """Main simulation loop"""
        self.running = True
        logger.info("🚀 Starting enhanced telemetry simulation...")
        
        # Initialize simulators
        self.initialize_simulators()
        
        # Start concurrent tasks
        tasks = [
            asyncio.create_task(self.simulate_random_sessions()),
            asyncio.create_task(self.publish_telemetry()),
        ]
        
        try:
            # Print manual control instructions
            print("\n" + "="*60)
            print("📱 TELEMETRY SIMULATOR CONTROLS")
            print("="*60)
            print("Available charger IDs: ", list(self.simulators.keys()))
            print("\nManual control examples (in another terminal):")
            print("python3 -c \"")
            print("from telemetry_simulator_enhanced import TelemetryManager")
            print("manager = TelemetryManager()")
            print("manager.manual_control(1, 'start_session', target_energy=50)")
            print("manager.manual_control(2, 'set_fault')")
            print("manager.manual_control(3, 'set_available')")
            print("\"")
            print("="*60 + "\n")
            
            # Run until interrupted
            await asyncio.gather(*tasks)
            
        except KeyboardInterrupt:
            logger.info("🛑 Simulation stopped by user")
            self.running = False
            
            # Cancel tasks
            for task in tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
        
        finally:
            # Cleanup
            await self.http_client.aclose()
            logger.info("🧹 Cleanup completed")

async def main():
    """Main function"""
    # Check if telemetry simulation is enabled
    if not getattr(settings, 'SIMULATE_TELEMETRY', True):
        logger.warning("Telemetry simulation is disabled in settings")
        return
    
    manager = TelemetryManager()
    
    try:
        await manager.run()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        logger.info("Telemetry simulator shutdown complete")

if __name__ == "__main__":
    # Create event loop and run
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Telemetry simulator stopped")
    except Exception as e:
        print(f"\n❌ Error: {e}")