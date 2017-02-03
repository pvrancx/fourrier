import pb_options as pb
from option_models import IntraOptionQLearner
import gym
import gym_pinball
from fourier import FourierBasis
import dill # allows pickling lambdas
import cPickle as pickle
import numpy as np
import argparse
import copy

def run_exp(exp_id,beta_high, beta_low, alpha, beta_eps,
            gamma=.99,
            epsilon=.01,
            order=5,
            n_steps=1000,
            log_steps = 1000,
            log_dir='.'):

    option_list = ['../options/option_[ 0.  0.  1.  1.]_[ 0.1  0.8  0.2  0.9].pkl', #upper left
           '../options/option_[ 0.  0.  1.  1.]_[ 0.8  0.8  0.9  0.9].pkl', #upper right
           '../options/option_[ 0.  0.  1.  1.]_[ 0.55  0.65  0.65  0.75].pkl', #center
           '../options/option_[ 0.  0.  1.  1.]_[ 0.25  0.2   0.35  0.3 ].pkl', #lower left
           '../options/option_[ 0.  0.  1.  1.]_[ 0.6  0.2  0.7  0.3].pkl', #lower right
           '../options/option_[ 0.6   0.    1.    0.35]_goal.pkl' # finish

    ]

    # load options
    options = []
    eps = 0.
    for f in option_list:
        options.append(pb.load_option(f,eps))

    init_fn = [ lambda obs: obs[1] > .6,
                lambda obs: obs[1] > .6,
                lambda obs: pb.in_rect(obs[:2],(0.,0.,1.,1.)),
                lambda obs: obs[0] < .6,
                lambda obs: pb.in_rect(obs[:2],(.2,.2,.7,.7)),
                lambda obs: pb.in_rect(obs[:2],(.6,0.,1.,.35))

                ]

    beta_fn = [ lambda obs: beta_high if pb.in_rect(obs[:2],(.1,.8,.2,.9)) else beta_low,
            lambda obs: beta_high if pb.in_rect(obs[:2],(.8,.8,.9,.9)) else beta_low,
            lambda obs: beta_high if pb.in_rect(obs[:2],(.55,.65,.65,.75)) else beta_low,
            lambda obs: beta_high if pb.in_rect(obs[:2],(.25,.2,.35,.3)) else beta_low,
            lambda obs: beta_high if pb.in_rect(obs[:2],(.6,.2,.7,.3)) else beta_low,
            lambda obs: beta_high if not pb.in_rect(obs[:2],(.6,0.,1.,.35)) else beta_low
        ]

    env = gym.make('PinBall-v0')
    n_actions = env.action_space.n

    low, high = env.observation_space.low, env.observation_space.high
    proj = FourierBasis(low, high, order=order)

    agent = IntraOptionQLearner(#env=env,
                            proj=proj,
                            options=options,
                            betas=beta_fn,
                            beta_eps = beta_eps,
                            inits=init_fn,
                            alpha=alpha,
                            gamma=gamma,
                            epsilon=epsilon)

    rew_log = []
    step_log = []
    theta_steps = []
    theta_log = []
    n_eps = 0
    ep_steps = 0
    ep_rew = 0.

    obs = env.reset()
    act = agent.start(obs)

    for steps in range(n_steps):
        obs_n, rew, done, _ = env.step(act)
        act = agent.update(obs_n, rew, done)

        if steps % log_steps == 0:
            theta_steps.append(steps)
            theta_log.append(copy.copy(agent.theta))
        ep_steps += 1
        ep_rew += rew
        if done:
            obs_n = env.reset()
            act = agent.start(obs)
            print 'episode %d -- steps: %d -- rew: %3.2f'%(n_eps,ep_steps,ep_rew)
            rew_log.append(ep_rew)
            step_log.append(ep_steps)
            ep_steps = 0
            ep_rew = 0.
            n_eps+=1

    log = {}
    log['steps'] = n_steps
    log['rewards'] = rew_log
    log['beta_low'] = beta_low
    log['beta_high'] = beta_high
    log['ep_steps'] = step_log
    log['order'] = order
    log['thetas'] = theta_log
    log['theta_final'] = copy.copy(agent.theta)
    log['agent_config'] = agent.get_config()
    print(log['agent_config'] )



    savefile = log_dir+'/log_'+str(exp_id)+'.pkl'
    with open(savefile,'wb') as f:
        pickle.dump(log,f)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-id", type=int, help="id")
    parser.add_argument("-alpha", type=float, help="learning rate")
    parser.add_argument("-beta1", type=float, help="beta1")
    parser.add_argument("-beta2", type=float, help="beta2")
    parser.add_argument("-beta_eps", type=float, help="beta bias")
    parser.add_argument("-log", type=str, help="log dir")

    args = parser.parse_args()

    run_exp(exp_id=args.id,
            alpha=args.alpha,
            beta_high=args.beta1,
            beta_low=args.beta2,
            beta_eps=args.beta_eps,
            log_dir=args.log)