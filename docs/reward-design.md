# Reward design

Twelve weighted terms. Two ask for motion; ten rule out cheap ways of producing
it. This is where the gait actually comes from — the network architecture is
generic, but these weights are the specification of what "walking" means.

| Term | Weight | What it is for |
|---|---:|---|
| `track_lin_vel_xy_exp` | **+1.50** | go where you are told |
| `track_ang_vel_z_exp` | **+0.75** | turn as commanded |
| `feet_air_time` | **+0.01** | take real steps, don't shuffle |
| `lin_vel_z_l2` | −2.00 | don't bounce vertically |
| `flat_orientation_l2` | −1.00 | keep the body level |
| `dof_pos_limits` | −0.50 | stay off the joint stops |
| `base_height` | −0.50 | hold stance height |
| `feet_stumble` | −0.50 | don't clip obstacle edges |
| `ang_vel_xy_l2` | −0.05 | no roll or pitch spin |
| `action_rate_l2` | −0.01 | smooth successive commands |
| `dof_torques_l2` | −2e-4 | save energy |
| `dof_acc_l2` | −2.5e-7 | no jerk |

Machine-readable copy: [`results/reward_terms.csv`](../results/reward_terms.csv).

## Why the weights span seven orders of magnitude

The penalties are not all measured in the same units. `dof_acc_l2` sums the
square of joint accelerations, which are numerically enormous — a coefficient of
2.5e-7 still produces a meaningful contribution. `flat_orientation_l2` sums the
square of a projected-gravity component bounded by 1. Weight magnitude alone says
nothing about a term's influence; weight × the term's typical scale does.

This is why the chart on the demo site plots bar length on a cube-root scale and
prints the true value beside every bar. A linear axis would render eight of the
twelve terms invisible.

## The shape of the problem

Only two terms are positive and meaningful. Left alone, tracking reward is easy
to game: a robot can hop, scrabble, drag a foot, or thrash its motors and still
move in roughly the right direction. Each penalty closes one of those doors:

- `lin_vel_z_l2` and `base_height` close **hopping**
- `feet_air_time` closes **shuffling** — it rewards genuine swing phases
- `feet_stumble` closes **dragging feet through obstacles**
- `dof_torques_l2` and `dof_acc_l2` close **brute-forcing it with the motors**
- `action_rate_l2` closes **high-frequency chattering**, which looks fine in
  simulation and destroys real hardware

The negative reward at the start of training is mostly these penalties: an
untrained policy flails, is penalised on every axis at once, and terminates early
on `base_contact`.

## Terminations

| Term | Time-out |
|---|---|
| `time_out` | yes — episode reaches its 20 s limit |
| `base_contact` | no — the body touched the ground, a real failure |

The distinction matters for bootstrapping: a time-out truncates the episode and
the value function should still bootstrap from the final state, whereas
`base_contact` is a true terminal state worth zero.
