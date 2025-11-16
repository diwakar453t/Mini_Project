"""
Telemetry simulator for demo purposes
Simulates real charger telemetry data and WebSocket updates
"""
import asyncio
import random
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List
import redis
import httpx
import os
import sys
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.config import settings
from app.models.charger import ChargerStatus
from app.models.booking import BookingStatus

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Redis connection for pub/sub
redis_client = None
try:
    redis_client = redis.from_url(settings.REDIS_URL)
    redis_client.ping()
    logger.info("✅ Connected to Redis")
except Exception as e:
    logger.error(f"❌ Failed to connect to Redis: {e}")

# HTTP client for API calls
http_client = httpx.AsyncClient(timeout=30.0)


class ChargerSimulator:
    """Simulate a single charger's telemetry"""
    
    def __init__(self, charger_id: int, charger_data: dict):
        self.charger_id = charger_id
        self.max_power_kw = charger_data.get("max_power_kw", 50)
        self.voltage = charger_data.get("voltage", 400)
        self.connector_type = charger_data.get("connector_type", "CCS")
        
        # Current state
        self.status = ChargerStatus.AVAILABLE
        self.current_power = 0.0
        self.current_voltage = self.voltage
        self.current_amperage = 0.0
        self.temperature = random.uniform(20, 35)
        self.session_id = None
        self.session_start_time = None
        self.energy_delivered = 0.0
        self.session_duration = 0
        
        # Simulation parameters
        self.last_update = time.time()
        self.error_probability = 0.001  # 0.1% chance of error
        self.maintenance_probability = 0.0001  # Very low chance
        
    def update_telemetry(self):
        """Update telemetry data based on current status"""
        now = time.time()
        time_delta = now - self.last_update
        self.last_update = now
        
        # Random status changes
        if self.status == ChargerStatus.AVAILABLE:
            # Small chance to start charging or go into maintenance
            if random.random() < 0.002:  # 0.2% chance per update
                self.start_charging_session()
            elif random.random() < self.maintenance_probability:
                self.status = ChargerStatus.MAINTENANCE
                
        elif self.status == ChargerStatus.IN_USE:
            # Continue charging session
            if self.session_start_time:
                self.session_duration = int((now - self.session_start_time) / 60)  # minutes
                
                # Energy delivered calculation (kWh)
                energy_per_second = self.current_power / 3600  # Convert kW to kWh per second
                self.energy_delivered += energy_per_second * time_delta
                
                # Charging profile simulation (starts high, tapers off)
                if self.session_duration < 30:  # First 30 minutes
                    target_power = self.max_power_kw * random.uniform(0.8, 1.0)
                elif self.session_duration < 60:  # Next 30 minutes
                    target_power = self.max_power_kw * random.uniform(0.6, 0.8)
                else:  # After 1 hour
                    target_power = self.max_power_kw * random.uniform(0.3, 0.6)
                
                # Gradually adjust power to target
                power_diff = target_power - self.current_power
                self.current_power += power_diff * 0.1  # Smooth transition
                
                # Calculate current based on power and voltage
                self.current_amperage = (self.current_power * 1000) / self.current_voltage if self.current_voltage > 0 else 0
                
                # Temperature increases with power
                base_temp = 25
                temp_increase = (self.current_power / self.max_power_kw) * 15  # Up to 15°C increase
                self.temperature = base_temp + temp_increase + random.uniform(-2, 2)
                
                # Random chance to complete session
                if random.random() < 0.005:  # 0.5% chance per update
                    self.stop_charging_session()
                    
        elif self.status == ChargerStatus.MAINTENANCE:
            # Eventually come back online
            if random.random() < 0.01:  # 1% chance per update
                self.status = ChargerStatus.AVAILABLE
                self.current_power = 0.0
                self.current_amperage = 0.0
                self.temperature = random.uniform(20, 30)
                
        elif self.status == ChargerStatus.FAULT:
            # Eventually recover from fault
            if random.random() < 0.02:  # 2% chance per update
                self.status = ChargerStatus.AVAILABLE
                self.current_power = 0.0
                self.current_amperage = 0.0
                
        # Random faults
        if random.random() < self.error_probability:
            self.status = ChargerStatus.FAULT
            self.current_power = 0.0
            self.current_amperage = 0.0
            if self.session_id:
                self.stop_charging_session()
                
        # Voltage fluctuations
        if self.status == ChargerStatus.IN_USE:
            self.current_voltage = self.voltage + random.uniform(-5, 5)
        else:
            self.current_voltage = self.voltage
            
    def start_charging_session(self):
        """Start a new charging session"""
        self.status = ChargerStatus.IN_USE
        self.session_id = f"sim_{self.charger_id}_{int(time.time())}"
        self.session_start_time = time.time()
        self.energy_delivered = 0.0
        self.session_duration = 0
        self.current_power = 0.0  # Will ramp up gradually
        
        logger.info(f"🔌 Charger {self.charger_id} started charging session: {self.session_id}")
        
    def stop_charging_session(self):
        """Stop current charging session"""
        if self.session_id:
            logger.info(f"🔋 Charger {self.charger_id} completed charging session: {self.session_id} "
                       f"({self.energy_delivered:.2f} kWh, {self.session_duration} min)")
            
        self.status = ChargerStatus.AVAILABLE
        self.session_id = None
        self.session_start_time = None
        self.current_power = 0.0
        self.current_amperage = 0.0
        self.energy_delivered = 0.0
        self.session_duration = 0
        self.temperature = random.uniform(20, 35)
        
    def get_telemetry_data(self) -> dict:
        """Get current telemetry data"""
        return {
            "charger_id": self.charger_id,
            "timestamp": datetime.utcnow().isoformat(),
            "status": self.status.value,
            "power_output_kw": round(self.current_power, 2),
            "voltage_v": round(self.current_voltage, 1),
            "current_a": round(self.current_amperage, 2),
            "temperature_c": round(self.temperature, 1),
            "session_id": self.session_id,
            "energy_delivered_kwh": round(self.energy_delivered, 3),
            "session_duration_minutes": self.session_duration,
            "error_code": None if self.status != ChargerStatus.FAULT else f"ERR_{random.randint(100, 999)}",
            "connectivity_status": "online",
            "signal_strength": random.randint(70, 100),
            "firmware_version": "1.2.3",
            "last_heartbeat": datetime.utcnow().isoformat(),
        }


class TelemetryManager:
    """Manage multiple charger simulators"""
    
    def __init__(self):
        self.simulators: Dict[int, ChargerSimulator] = {}
        self.running = False
        
    async def initialize_chargers(self):
        """Fetch charger data from API and initialize simulators"""
        try:
            # Get charger list from API
            response = await http_client.get(f"{settings.BACKEND_URL}/api/v1/chargers?limit=100")
            if response.status_code == 200:
                chargers = response.json()
                
                for charger in chargers:
                    simulator = ChargerSimulator(charger["id"], charger)
                    self.simulators[charger["id"]] = simulator
                    
                logger.info(f"✅ Initialized {len(self.simulators)} charger simulators")
            else:
                logger.error(f"❌ Failed to fetch chargers: {response.status_code}")
                
        except Exception as e:
            logger.error(f"❌ Error initializing chargers: {e}")
            # Create some mock chargers for demo
            for i in range(1, 11):
                mock_charger = {
                    "id": i,
                    "max_power_kw": random.choice([7, 22, 50, 120]),
                    "voltage": random.choice([220, 400, 480]),
                    "connector_type": random.choice(["CCS", "CHAdeMO", "Type2"])
                }
                self.simulators[i] = ChargerSimulator(i, mock_charger)
            
            logger.info(f"✅ Created {len(self.simulators)} mock charger simulators")
            
    async def update_all_telemetry(self):
        """Update telemetry for all simulators"""
        for simulator in self.simulators.values():
            simulator.update_telemetry()
            
            # Get telemetry data
            telemetry = simulator.get_telemetry_data()
            
            # Publish to Redis for WebSocket subscribers
            if redis_client:
                try:
                    channel = f"charger_telemetry_{simulator.charger_id}"
                    redis_client.publish(channel, json.dumps(telemetry))
                except Exception as e:
                    logger.error(f"❌ Failed to publish telemetry for charger {simulator.charger_id}: {e}")
            
            # Store in database (simulate API call)
            try:
                # In a real system, this would be a proper API endpoint
                # For demo, we'll just log significant events
                if simulator.session_id and random.random() < 0.1:  # Log 10% of active sessions
                    logger.info(f"📊 Charger {simulator.charger_id}: "
                               f"{telemetry['power_output_kw']}kW, "
                               f"{telemetry['energy_delivered_kwh']}kWh, "
                               f"{telemetry['session_duration_minutes']}min")
                               
            except Exception as e:
                logger.error(f"❌ Error storing telemetry for charger {simulator.charger_id}: {e}")
                
    async def run_simulation(self):
        """Main simulation loop"""
        self.running = True
        logger.info("🚀 Starting telemetry simulation...")
        
        while self.running:
            try:
                await self.update_all_telemetry()
                await asyncio.sleep(settings.TELEMETRY_UPDATE_INTERVAL)
                
            except KeyboardInterrupt:
                logger.info("🛑 Stopping simulation...")
                self.running = False
                break
            except Exception as e:
                logger.error(f"❌ Simulation error: {e}")
                await asyncio.sleep(5)  # Wait before retrying
                
    def stop_simulation(self):
        """Stop the simulation"""
        self.running = False


async def main():
    """Main function"""
    logger.info("🔧 Initializing telemetry simulator...")
    
    manager = TelemetryManager()
    
    try:
        # Initialize chargers
        await manager.initialize_chargers()
        
        # Run simulation
        await manager.run_simulation()
        
    except KeyboardInterrupt:
        logger.info("🛑 Simulation stopped by user")
    except Exception as e:
        logger.error(f"❌ Fatal error: {e}")
    finally:
        # Cleanup
        await http_client.aclose()
        if redis_client:
            redis_client.close()
        logger.info("🧹 Cleanup completed")


if __name__ == "__main__":
    asyncio.run(main())