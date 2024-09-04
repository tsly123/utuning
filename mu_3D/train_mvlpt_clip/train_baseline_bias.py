import argparse
import torch
import os
import shutil

from dassl.utils import setup_logger, set_random_seed, collect_env_info
from dassl.config import get_cfg_default
from dassl.engine import build_trainer

# custom
import datasets.oxford_pets
import datasets.oxford_flowers
# import datasets.fgvc_aircraft
# import datasets.dtd
# import datasets.eurosat
# import datasets.stanford_cars
# import datasets.food101
# import datasets.sun397
# import datasets.caltech101
# import datasets.ucf101
# import datasets.imagenet
#
# import datasets.imagenet_sketch
# import datasets.imagenetv2
# import datasets.imagenet_a
# import datasets.imagenet_r
# import datasets.imagenet_21k
# import datasets.bamboo

# import trainers.coop
# import trainers.cocoop
# import trainers.zsclip
# import trainers.mvlpt

import trainers.baseline_bias

###################################
# import datasets.bloodmnist
# import datasets.breastmnist
# import datasets.chestmnist
# import datasets.dermamnist
# import datasets.octmnist
# import datasets.organamnist
# import datasets.organcmnist
# import datasets.organsmnist
# import datasets.pathmnist
# import datasets.pneumoniamnist
# import datasets.retinamnist
# import datasets.tissuemnist

import datasets.adrenalmnist3d
import datasets.vesselmnist3d
import datasets.nodulemnist3d
import datasets.luna16
import datasets.deeplesion
import datasets.luna22
import datasets.braincell
import datasets.lidcidri
import datasets.prostatex
import datasets.rsna
###################################

def copy_files(cfg):
    print("Copy trainer file")
    trainer_dir = cfg.OUTPUT_DIR+'/trainer_files'
    os.makedirs(trainer_dir, exist_ok=True)
    trainer_scr = '/project/hnguyen2/stly/code/prompting/MVLPT_3D/trainers/baseline_bias.py'
    trainer_dst = trainer_dir+'/baseline_bias.py'
    shutil.copyfile(trainer_scr, trainer_dst)

    clip_model_scr = '/project/hnguyen2/stly/code/prompting/MVLPT_3D/clip/model.py'
    clip_model_dst = trainer_dir + '/clip_model.py'
    shutil.copyfile(clip_model_scr, clip_model_dst)

    cfg_scr = '/project/hnguyen2/stly/code/prompting/MVLPT_3D/configs/trainers/MVLPT/vit_b16_3d.yaml'
    cfg_dst = trainer_dir + '/vit_b16_3d.yaml'
    shutil.copyfile(cfg_scr, cfg_dst)

def print_args(args, cfg):
    print("***************")
    print("** Arguments **")
    print("***************")
    optkeys = list(args.__dict__.keys())
    optkeys.sort()
    for key in optkeys:
        print("{}: {}".format(key, args.__dict__[key]))
    print("************")
    print("** Config **")
    print("************")
    print(cfg)


def reset_cfg(cfg, args):
    if args.root:
        cfg.DATASET.ROOT = args.root

    if args.output_dir:
        cfg.OUTPUT_DIR = args.output_dir

    if args.resume:
        cfg.RESUME = args.resume

    if args.seed:
        cfg.SEED = args.seed
        cfg.DATASET.RANDOM_SEED_SAMPLING = args.seed

    if args.source_domains:
        cfg.DATASET.SOURCE_DOMAINS = args.source_domains

    if args.target_domains:
        cfg.DATASET.TARGET_DOMAINS = args.target_domains

    if args.transforms:
        cfg.INPUT.TRANSFORMS = args.transforms

    if args.trainer:
        cfg.TRAINER.NAME = args.trainer

    if args.backbone:
        cfg.MODEL.BACKBONE.NAME = args.backbone

    if args.head:
        cfg.MODEL.HEAD.NAME = args.head

    if args.dataset:
        cfg.DATASET.DATASET = args.dataset

    if args.shots:
        cfg.DATASET.NUM_SAMPLES_PER_CLASS = args.shots
        cfg.DATASET.NUM_SHOTS = args.shots

    if args.multi_task:
        cfg.DATASET.MULTITASK = args.multi_task

    if args.multi_task_label_pertask:
        cfg.DATASET.MULTITASK_LABEL_PERTASK = args.multi_task_label_pertask

    if args.dataset_coop:
        cfg.DATASET.COOP = args.dataset_coop

    if args.cut_contextlen:
        cfg.TRAINER.CUT_CONTEXTLEN = args.cut_contextlen

    if args.act_ckpt:
        cfg.TRAINER.ACT_CKPT = args.act_ckpt

    if args.multi_task_evalkey != 'average':
        cfg.DATASET.MULTITASK_EVALKEY = args.multi_task_evalkey

    if args.lr is not None:
        cfg.OPTIM.LR = args.lr
    else:
        cfg.OPTIM.LR = 2e-3

    if args.get_feat != "None":
        cfg.get_feat = args.get_feat

def extend_cfg(cfg):
    """
    Add new config variables.

    E.g.
        from yacs.config import CfgNode as CN
        cfg.TRAINER.MY_MODEL = CN()
        cfg.TRAINER.MY_MODEL.PARAM_A = 1.
        cfg.TRAINER.MY_MODEL.PARAM_B = 0.5
        cfg.TRAINER.MY_MODEL.PARAM_C = False
    """
    from yacs.config import CfgNode as CN
    prec = 'fp16'
    cfg.TRAINER.COOP = CN()
    cfg.TRAINER.COOP.N_CTX = 16  # number of context vectors
    cfg.TRAINER.COOP.CSC = False  # class-specific context
    cfg.TRAINER.COOP.CTX_INIT = ""  # initialization words
    cfg.TRAINER.COOP.PREC = "fp16"  # fp16, fp32, amp
    cfg.TRAINER.COOP.CLASS_TOKEN_POSITION = "end"  # 'middle' or 'end' or 'front'

    cfg.TRAINER.COCOOP = CN()
    cfg.TRAINER.COCOOP.N_CTX = 16  # number of context vectors
    cfg.TRAINER.COCOOP.CTX_INIT = ""  # initialization words
    cfg.TRAINER.COCOOP.PREC = "fp16"  # fp16, fp32, amp

    cfg.TRAINER.MVLPT = CN()
    cfg.TRAINER.MVLPT.PREC = prec  # fp16, fp32, amp
    cfg.TRAINER.MVLPT.PROJECT_METHOD = 'transformer'  # could be identity / mlp / transformer
    cfg.TRAINER.MVLPT.PROJECT_DIM = 128  # if coop/vpt dimension doesnot match, project to vpt/coop

    cfg.TRAINER.MVLPT.VPT = CN()
    cfg.TRAINER.MVLPT.VPT.N_CTX = 0  # number of context vectors
    cfg.TRAINER.MVLPT.VPT.CSC = False  # class-specific context
    cfg.TRAINER.MVLPT.VPT.CTX_INIT = ""  # initialization words
    cfg.TRAINER.MVLPT.VPT.DROPOUT = 0.0  # dropout
    cfg.TRAINER.MVLPT.VPT.PROJECT = -1  # Project
    cfg.TRAINER.MVLPT.VPT.DEEP = True  # Deep or shallow

    cfg.TRAINER.MVLPT.COOP = CN()
    cfg.TRAINER.MVLPT.COOP.N_CTX = 0  # number of context vectors
    cfg.TRAINER.MVLPT.COOP.CSC = False  # class-specific context
    cfg.TRAINER.MVLPT.COOP.CTX_INIT = ""  # initialization words
    cfg.TRAINER.MVLPT.COOP.CLASS_TOKEN_POSITION = "middle"  # 'middle' or 'end' or 'front'

    cfg.TRAINER.MVLPT.COCOOP = CN()
    cfg.TRAINER.MVLPT.COCOOP.N_CTX = 0  # number of context vectors
    cfg.TRAINER.MVLPT.COCOOP.CTX_INIT = ""  # initialization words
    cfg.TRAINER.MVLPT.COCOOP.PREC = "fp16"  # fp16, fp32, amp

    cfg.TRAINER.Baseline_bias = CN()
    cfg.TRAINER.Baseline_bias.PREC = prec  # fp16, fp32, amp
    cfg.TRAINER.Baseline_bias.PROJECT_METHOD = 'transformer'  # could be identity / mlp / transformer
    cfg.TRAINER.Baseline_bias.PROJECT_DIM = 128  # if coop/vpt dimension doesnot match, project to vpt/coop

    cfg.DATASET.SUBSAMPLE_CLASSES = "all"  # all, base or new
    cfg.DATASET.NUM_SAMPLES_PER_CLASS = 20
    cfg.DATASET.DATASET = ""
    cfg.DATASET.RANDOM_SEED_SAMPLING = 1
    cfg.DATASET.VAL_SET = "val"
    cfg.DATASET.TRAIN_SET = "train"
    cfg.DATASET.TEST_SET = "test"
    cfg.DATASET.CENTER_CROP = False

    cfg.TRAINER.CUT_CONTEXTLEN = False
    cfg.TRAINER.ACT_CKPT = 1

    cfg.DATASET.COOP = False
    cfg.DATASET.MULTITASK = False
    cfg.DATASET.MULTITASK_LABEL_PERTASK = False
    cfg.DATASET.MULTITASK_EVALKEY = 'average'


def setup_cfg(args):
    cfg = get_cfg_default()
    extend_cfg(cfg)

    # 1. From the dataset config file
    if args.dataset_config_file:
        cfg.merge_from_file(args.dataset_config_file)

    # 2. From the method config file
    if args.config_file:
        cfg.merge_from_file(args.config_file)

    # 3. From input arguments
    reset_cfg(cfg, args)

    # 4. From optional input arguments
    cfg.merge_from_list(args.opts)

    cfg.freeze()

    return cfg


def main(args):
    cfg = setup_cfg(args)
    if cfg.SEED >= 0:
        print("Setting fixed seed: {}".format(cfg.SEED))
        set_random_seed(cfg.SEED)

    if args.get_feat != "None":
        if torch.cuda.is_available() and cfg.USE_CUDA:
            torch.backends.cudnn.benchmark = True

        print_args(args, cfg)
        print("Collecting env info ...")
        print("** System info **\n{}\n".format(collect_env_info()))

        trainer = build_trainer(cfg)

        print('Extract feature with avg_ckpt path', args.get_feat)
        assert os.path.isdir(args.get_feat)
        print('\nEtract with best ACC')
        trainer.load_model_feat(args.get_feat, name_model='model-best.pth.tar')
        # trainer.get_feat(name_model='model-best.pth.tar')
        trainer.test(get_output=True)

        print('\nEtract with last epoch')
        save_name = f'model.pth.tar-{cfg.OPTIM.MAX_EPOCH}'
        trainer.load_model_feat(args.get_feat, name_model=save_name)
        # trainer.get_feat(name_model=save_name)
        trainer.test(get_output=True)

        print('\nEtract with best AUC')
        trainer.load_model_feat(args.get_feat, name_model='model-best-auc.pth.tar')
        # trainer.get_feat(name_model='model-best-auc.pth.tar')
        trainer.test(get_output=True)

        print('\nEtract with best balance')
        trainer.load_model_feat(args.get_feat, name_model='model-best-balance.pth.tar')
        # trainer.get_feat(name_model='model-best-balance.pth.tar')
        trainer.test(get_output=True)

        print('\nEtract with best ACC with AUC > 50')
        trainer.load_model_feat(args.get_feat, name_model='model-best-50auc.pth.tar')
        # trainer.get_feat(name_model='model-best-50auc.pth.tar')
        trainer.test(get_output=True)
        return

    setup_logger(cfg.OUTPUT_DIR)

    if torch.cuda.is_available() and cfg.USE_CUDA:
        torch.backends.cudnn.benchmark = True

    print_args(args, cfg)
    print("Collecting env info ...")
    print("** System info **\n{}\n".format(collect_env_info()))

    trainer = build_trainer(cfg)
    # print(trainer._models)
    # print(trainer.model)

    if args.eval_only != "None":
        print('Eval only: eval dir', args.eval_only)
        # trainer.load_model(args.model_dir, epoch=args.load_epoch)
        assert os.path.isdir(args.eval_only)
        print('Eval with best ACC')
        trainer.load_model(args.eval_only, name_model='model-best.pth.tar')
        trainer.test()

        print('Eval with last epoch')
        save_name = f'model.pth.tar-{cfg.OPTIM.MAX_EPOCH}'
        trainer.load_model(args.eval_only, name_model=save_name)
        trainer.test()

        print('Eval with best AUC')
        trainer.load_model(args.eval_only, name_model='model-best-auc.pth.tar')
        trainer.test()

        print('Eval with best balance')
        trainer.load_model(args.eval_only, name_model='model-best-balance.pth.tar')
        trainer.test()

        print('Eval with best ACC with AUC > 50')
        trainer.load_model(args.eval_only, name_model='model-best-50auc.pth.tar')
        trainer.test()
        return

    if args.model_dir:
        trainer.load_model(args.model_dir)

    copy_files(cfg)
    
    if not args.no_train:
        trainer.train()

    # print(trainer.model)

    # trainer.load_clip_to_cpu(cfg)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=str, default="", help="path to dataset")
    parser.add_argument("--output-dir", type=str, default="", help="output directory")
    parser.add_argument(
        "--resume",
        type=str,
        default="",
        help="checkpoint directory (from which the training resumes)",
    )
    parser.add_argument(
        "--seed", type=int, default=-1, help="only positive value enables a fixed seed"
    )
    parser.add_argument(
        "--source-domains", type=str, nargs="+", help="source domains for DA/DG"
    )
    parser.add_argument(
        "--target-domains", type=str, nargs="+", help="target domains for DA/DG"
    )
    parser.add_argument(
        "--transforms", type=str, nargs="+", help="data augmentation methods"
    )
    parser.add_argument(
        "--config-file", type=str, default="", help="path to config file"
    )
    parser.add_argument(
        "--dataset-config-file",
        type=str,
        default="",
        help="path to config file for dataset setup",
    )
    parser.add_argument(
        "--dataset",
        type=str,
        default="",
        help="name of task",
    )
    parser.add_argument(
        "--shots",
        type=int,
        help="few shot",
    )
    parser.add_argument("--trainer", type=str, default="MVLPT", help="name of trainer")
    parser.add_argument("--backbone", type=str, default="", help="name of CNN backbone")
    parser.add_argument("--head", type=str, default="", help="name of head")
    # parser.add_argument("--eval-only", action="store_true", help="evaluation only")
    parser.add_argument("--eval-only", type=str, default="None", help="evaluation only")
    parser.add_argument(
        "--model-dir",
        type=str,
        default="",
        help="load model from this directory for eval-only mode",
    )
    parser.add_argument(
        "--load-epoch", type=int, help="load model weights at this epoch for evaluation"
    )
    parser.add_argument(
        "--no-train", action="store_true", help="do not call trainer.train()"
    )
    parser.add_argument("--multi-task", action="store_true")
    parser.add_argument("--multi-task-label_pertask", action="store_true")
    parser.add_argument("--multi-task-evalkey", type=str, default='average')

    parser.add_argument("--dataset-coop", action="store_true")
    parser.add_argument("--cut-contextlen", action="store_true")
    parser.add_argument("--act-ckpt", type=int, default=1)

    parser.add_argument(
        "opts",
        default=None,
        nargs=argparse.REMAINDER,
        help="modify config options using the command-line",
    )

    parser.add_argument("--lr", type=float, default=2e-3)
    parser.add_argument("--get-feat", type=str, default="None",
                        help="directory path, similar as args.eval_only")
    args = parser.parse_args()
    main(args)
