from store import FAISSVectorStore
from rag import CertRAG
import dotenv

dotenv.load_dotenv()

faiss_vector_store = FAISSVectorStore()
requirement = """Goal: Notify the surrounding people, cyclists and other road users of the Vehicle's reverse movement by external sound.
Description:
AVAS sound starts when moving in R starts (vehicle speed > 0).
The driver is in the Vehicle, the Vehicle is in the R drive mode and reversing at any speed, an external soundtrack notifies surrounding road users about the movement of the Vehicle in reverse, so that an approaching Vehicle can be identified by ear. Only one sound is available to the driver. The function cannot be disabled.
Preconditions:
1) Vehicle is in working condition.
2) Vehicle's AVAS system is working properly.
3) Vehicle is in the R drive mode and is moving at any speed or standing still.
4) There is no audio track selection, only one audio track is available.
Main scenario:
1) While driving the Vehicle in the R drive mode (vehicle speed > 0), it notifies the surrounding road users with an out_27.AVAS about reversing;
2) When switching the drive mode from R to any other or the Vehicle speed 0 out_27.AVAS is disabled.
Deactivation (Stopping, Cancelling)
Driver stops pressing acceleration pedal and the vehicle's speed is equal 0
Driver stops moving in reverse
"""

# identified_objects = faiss_vector_store.search_similar(requirement)
# for obj, score in identified_objects:
#     print(f"Score: {score}\n Object: {obj}\n =========================\n")

cert_rag = CertRAG(rag_type="default")

print(cert_rag.cert_documents(requirement))
