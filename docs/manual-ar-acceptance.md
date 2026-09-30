# Manual AR acceptance

Automated tests cannot prove that an AR cue is physically aligned with a real corridor. Complete this check before calling a build field-ready.

## Equipment and setup

- One ARCore-certified Android phone running the debug or release candidate.
- One published venue containing a calibrated floor, at least one turn, and destinations at both route ends.
- The phone and backend on the same network, or a map package cached before disconnecting.

Record the app version, phone model, Android version, venue, map version, tester, and date with the result.

## Procedure

1. Open the venue, place the start pin at a known corridor position, and point the facing control along the physical corridor.
2. Select a destination whose route includes a turn, then compare the route preview with the published graph.
3. Start AR. Confirm that one cue points toward the next route segment and remains stable during small translations and rotations.
4. Walk the route at normal speed. Confirm the cue advances after the turn and that remaining distance decreases without sudden large jumps.
5. Approach the destination door. Confirm arrival appears within approximately 2 metres of its graph node.
6. Navigate the same route in reverse.
7. Cover the camera or otherwise force ARCore out of `TRACKING` for longer than one second. Confirm all AR cues disappear and the app asks for position again.
8. Set the pin and facing direction again. Confirm navigation resumes from the new pose with a sensible cue.
9. Deny camera permission or test on a non-AR device. Confirm the complete 2D route remains usable.
10. Close an edge as a manager, refresh the visitor map, and confirm routing no longer uses that edge.

## Pass criteria

- No arrow points through a wall or opposite the selected route.
- Cues disappear whenever tracking is not reliable.
- The 2D map remains usable during every AR failure.
- Both route directions and the closed-edge refresh behave as documented.
- Arrival is triggered at the destination door rather than the room centre.

Any failure records the map version, start pose, destination, and reproduction steps. Transform or graph failures block release; cosmetic instability that does not misdirect the visitor must still be tracked before wider testing.
