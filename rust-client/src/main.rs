use clap::Parser;
use tonic::Request;

pub mod psu {
    tonic::include_proto!("sonic.psu.v1");
}

use psu::psu_service_client::PsuServiceClient;
use psu::*;

#[derive(Parser, Debug)]
#[command(name = "psu-client", about = "SONiC PSU gRPC test client")]
struct Args {
    /// gRPC server address
    #[arg(short, long, default_value = "http://127.0.0.1:50051")]
    addr: String,

    /// Number of PSUs to query
    #[arg(short, long, default_value_t = 2)]
    num_psus: i32,
}

fn separator(title: &str) {
    println!("\n{}", "─".repeat(60));
    println!("  {title}");
    println!("{}", "─".repeat(60));
}

fn banner(title: &str) {
    println!("\n{}", "═".repeat(60));
    println!("  {title}");
    println!("{}", "═".repeat(60));
}

macro_rules! call {
    ($label:expr, $expr:expr) => {
        match $expr.await {
            Ok(resp) => {
                println!("  {}: {:?}", $label, resp.into_inner());
            }
            Err(e) => {
                println!("  {}: ERROR [{}] {}", $label, e.code(), e.message());
            }
        }
    };
}

#[tokio::main]
async fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args = Args::parse();
    let mut client = PsuServiceClient::connect(args.addr.clone()).await?;

    println!("Connected to {}", args.addr);

    // ── Per-PSU RPCs ────────────────────────────────────────────
    for psu in 0..args.num_psus {
        banner(&format!("PSU {psu}"));

        // DeviceBase
        separator("DeviceBase Methods");
        call!("get_name",
            client.get_name(Request::new(GetNameRequest { psu_index: psu })));
        call!("get_presence",
            client.get_presence(Request::new(GetPresenceRequest { psu_index: psu })));
        call!("get_model",
            client.get_model(Request::new(GetModelRequest { psu_index: psu })));
        call!("get_serial",
            client.get_serial(Request::new(GetSerialRequest { psu_index: psu })));
        call!("get_revision",
            client.get_revision(Request::new(GetRevisionRequest { psu_index: psu })));
        call!("get_status",
            client.get_status(Request::new(GetStatusRequest { psu_index: psu })));
        call!("get_position_in_parent",
            client.get_position_in_parent(Request::new(GetPositionInParentRequest { psu_index: psu })));
        call!("is_replaceable",
            client.is_replaceable(Request::new(IsReplaceableRequest { psu_index: psu })));

        // Fans
        separator("Fan Methods");
        call!("get_num_fans",
            client.get_num_fans(Request::new(GetNumFansRequest { psu_index: psu })));
        call!("get_all_fans",
            client.get_all_fans(Request::new(GetAllFansRequest { psu_index: psu })));
        call!("get_fan(0)",
            client.get_fan(Request::new(GetFanRequest { psu_index: psu, fan_index: 0 })));
        call!("get_fan(99) [expect error]",
            client.get_fan(Request::new(GetFanRequest { psu_index: psu, fan_index: 99 })));

        // Thermals
        separator("Thermal Methods");
        call!("get_num_thermals",
            client.get_num_thermals(Request::new(GetNumThermalsRequest { psu_index: psu })));
        call!("get_all_thermals",
            client.get_all_thermals(Request::new(GetAllThermalsRequest { psu_index: psu })));
        call!("get_thermal(0)",
            client.get_thermal(Request::new(GetThermalRequest { psu_index: psu, thermal_index: 0 })));
        call!("get_thermal(1)",
            client.get_thermal(Request::new(GetThermalRequest { psu_index: psu, thermal_index: 1 })));
        call!("get_thermal(99) [expect error]",
            client.get_thermal(Request::new(GetThermalRequest { psu_index: psu, thermal_index: 99 })));

        // Electrical (output)
        separator("Electrical (Output)");
        call!("get_voltage",
            client.get_voltage(Request::new(GetVoltageRequest { psu_index: psu })));
        call!("get_current",
            client.get_current(Request::new(GetCurrentRequest { psu_index: psu })));
        call!("get_power",
            client.get_power(Request::new(GetPowerRequest { psu_index: psu })));
        call!("get_powergood_status",
            client.get_powergood_status(Request::new(GetPowergoodStatusRequest { psu_index: psu })));

        // Electrical (input)
        separator("Electrical (Input)");
        call!("get_input_voltage",
            client.get_input_voltage(Request::new(GetInputVoltageRequest { psu_index: psu })));
        call!("get_input_current",
            client.get_input_current(Request::new(GetInputCurrentRequest { psu_index: psu })));

        // Temperature & thresholds
        separator("Temperature & Thresholds");
        call!("get_temperature",
            client.get_temperature(Request::new(GetTemperatureRequest { psu_index: psu })));
        call!("get_temperature_high_threshold",
            client.get_temperature_high_threshold(Request::new(GetTemperatureHighThresholdRequest { psu_index: psu })));
        call!("get_voltage_high_threshold",
            client.get_voltage_high_threshold(Request::new(GetVoltageHighThresholdRequest { psu_index: psu })));
        call!("get_voltage_low_threshold",
            client.get_voltage_low_threshold(Request::new(GetVoltageLowThresholdRequest { psu_index: psu })));
        call!("get_maximum_supplied_power",
            client.get_maximum_supplied_power(Request::new(GetMaximumSuppliedPowerRequest { psu_index: psu })));
        call!("get_psu_power_warning_suppress_threshold",
            client.get_psu_power_warning_suppress_threshold(Request::new(GetPsuPowerWarningSuppressThresholdRequest { psu_index: psu })));
        call!("get_psu_power_critical_threshold",
            client.get_psu_power_critical_threshold(Request::new(GetPsuPowerCriticalThresholdRequest { psu_index: psu })));

        // Status LED
        separator("Status LED");
        call!("get_status_led",
            client.get_status_led(Request::new(GetStatusLedRequest { psu_index: psu })));
        call!("set_status_led('amber')",
            client.set_status_led(Request::new(SetStatusLedRequest { psu_index: psu, color: "amber".into() })));
        call!("get_status_led (after set)",
            client.get_status_led(Request::new(GetStatusLedRequest { psu_index: psu })));
        call!("set_status_led('purple') [expect error]",
            client.set_status_led(Request::new(SetStatusLedRequest { psu_index: psu, color: "purple".into() })));
    }

    // ── Master LED (class-level) ────────────────────────────────
    banner("Master LED (class-level)");
    call!("get_status_master_led",
        client.get_status_master_led(Request::new(GetStatusMasterLedRequest {})));
    call!("set_status_master_led('red')",
        client.set_status_master_led(Request::new(SetStatusMasterLedRequest { color: "red".into() })));
    call!("get_status_master_led (after set)",
        client.get_status_master_led(Request::new(GetStatusMasterLedRequest {})));
    call!("set_status_master_led('blue') [expect error]",
        client.set_status_master_led(Request::new(SetStatusMasterLedRequest { color: "blue".into() })));

    // ── Invalid PSU index ───────────────────────────────────────
    banner("Error Handling — Invalid PSU Index");
    call!("get_name(psu=99) [expect error]",
        client.get_name(Request::new(GetNameRequest { psu_index: 99 })));

    banner("All RPCs tested ✓");

    Ok(())
}
