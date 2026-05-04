const path = require("path");
const fs = require("fs");
const { Web3 } = require("web3");

const RPC_URL = process.env.GANACHE_RPC_URL || "http://127.0.0.1:7545";
const web3 = new Web3(RPC_URL);

function loadArtifact() {
  const artifactPath = path.resolve(__dirname, "..", "contracts", "artifacts", "SimpleUserFlow.json");
  const raw = fs.readFileSync(artifactPath, "utf8");
  const artifact = JSON.parse(raw);
  const abi = artifact.abi;
  const bytecode = "0x" + artifact.data.bytecode.object.replace(/^0x/, "");
  if (!abi || !Array.isArray(abi) || !bytecode || bytecode === "0x") {
    throw new Error("SimpleUserFlow artifact missing ABI/bytecode");
  }
  return { abi, bytecode };
}

function loadLegacyBytecodeFromScript() {
  const scriptPath = path.resolve(__dirname, "test_simple_user_flow.js");
  const content = fs.readFileSync(scriptPath, "utf8");
  const match = content.match(/const\s+(?:SIMPLE_USER_FLOW_BYTECODE|BYTECODE)\s*=\s*"([^"]+)"/);
  if (!match || !match[1]) {
    throw new Error("Cannot find legacy bytecode in test_simple_user_flow.js");
  }
  return match[1];
}

async function deploySimple(contract, bytecode, deployer) {
  return contract.deploy({ data: bytecode }).send({ from: deployer, gas: 4_500_000 });
}

async function main() {
  const { abi, bytecode } = loadArtifact();
  const accounts = await web3.eth.getAccounts();
  if (!accounts || accounts.length === 0) {
    throw new Error("No accounts from Ganache");
  }
  const deployer = accounts[0];
  const verifier = accounts[1] || accounts[0];

  console.log("RPC:", RPC_URL);
  console.log("deployer:", deployer);

  const contract = new web3.eth.Contract(abi);
  let instance;
  try {
    instance = await deploySimple(contract, bytecode, deployer);
  } catch (error) {
    const rawMessage = (error && error.message ? error.message : String(error)).toLowerCase();
    if (!rawMessage.includes("invalid opcode")) {
      throw error;
    }
    console.log("[WARN] artifact bytecode invalid opcode on current Ganache, fallback to legacy bytecode...");
    const legacyBytecode = loadLegacyBytecodeFromScript();
    instance = await deploySimple(contract, legacyBytecode, deployer);
  }
  console.log("[OK] deployed:", instance.options.address);

  const tx1 = await instance.methods.register("ganache_user").send({ from: deployer, gas: 250000 });
  console.log("[OK] register tx:", tx1.transactionHash);

  const profile1 = await instance.methods.getMyProfile().call({ from: deployer });
  if (!profile1.exists) {
    throw new Error("getMyProfile.exists expected true");
  }
  console.log("[OK] profile after register:", profile1);

  const tx2 = await instance.methods.updateNickname("ganache_user_new").send({ from: deployer, gas: 250000 });
  console.log("[OK] updateNickname tx:", tx2.transactionHash);

  const profile2 = await instance.methods.getMyProfile().call({ from: deployer });
  if (profile2.nickname !== "ganache_user_new") {
    throw new Error(`nickname mismatch: ${profile2.nickname}`);
  }
  console.log("[OK] profile after update:", profile2);

  const registered = await instance.methods.isRegistered(deployer).call({ from: verifier });
  if (!registered) {
    throw new Error("isRegistered expected true");
  }
  console.log(`[OK] isRegistered(${deployer}):`, registered);
}

main().catch((err) => {
  console.error("[FAIL]", err && err.message ? err.message : err);
  process.exit(1);
});
