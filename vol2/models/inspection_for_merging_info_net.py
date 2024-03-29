import configparser
import importlib
import os
import sys
import timeit
import torch

# configuration
cnn_name: str = 'merging_info_net_custom_features'

experiment_n = 1
checkpoint_n = 15
which = 'test'
form = 'full_im'
limit_maxD = True
get_common_dataset = True
common_dataset_name = 'freiburg_tr_te'
example_num = 1
device = 'cuda'


def run(conf_file):
    # import all needed modules
    utils = importlib.import_module('vol2.models.utils')
    net = importlib.import_module('vol2.models.' + cnn_name + '.' + cnn_name)
    preprocess = importlib.import_module('preprocess')

    # create helpful paths
    experiment_directory = os.path.join(
        conf_file['PATHS']['saved_models'], 'vol2', cnn_name, 'experiment_' + str(experiment_n))
    checkpoint_filepath = os.path.join(
        experiment_directory, 'checkpoint_' + str(checkpoint_n) + '.tar')

    # load dataset
    if get_common_dataset:
        merged_dataset = utils.load_common_dataset(
            common_dataset_name, conf_file['PATHS']['common_datasets'])
    else:
        merged_dataset = utils.load_specific_dataset(experiment_directory)

    # create model
    if device == 'cpu':
        model_instance = net.model()
    else:
        model_instance = net.model().cuda()

    # restore weights
    checkpoint = torch.load(checkpoint_filepath)
    model_instance.load_state_dict(checkpoint['state_dict'])

    # restore training statistics
    stats = checkpoint['stats']

    # timeit
    start_time = timeit.default_timer()

    data_feeder = preprocess.dataset(merged_dataset, which, form, limit_maxD)
    imL, imR, dispL, maskL = data_feeder[example_num]
    print(imL.shape)
    imL = imL.unsqueeze(0).cuda()
    imR = imR.unsqueeze(0).cuda()
    max_limit = dispL.max()
    dispL = dispL.unsqueeze(0).cuda()
    maskL = maskL.bool().unsqueeze(0).cuda()

    max_disp = 192
    h = imL.shape[2]
    w = imL.shape[3]
    initial_scale = [max_disp, h, w]
    scales = [[round(max_disp/8), round(h/8), round(w/8)],
              [round(max_disp/16), round(h/16), round(w/16)],
              [round(max_disp/32), round(h/32), round(w/32)]]
    # scales = [[round(max_disp/4), round(h/4), round(w/4)],
    #           [round(max_disp/8), round(h/8), round(w/8)],
    #           [round(max_disp/16), round(h/16), round(w/16)]]
    
    prediction_from_scales = {0: ['after'],
                              1: ['after'],
                              2: ['after']}

    mae, err_pcg, imL_d, imR_d, volumes, volumes_dict, for_out_dict, predictions_dict = net.inspection(
        model_instance, initial_scale, scales, prediction_from_scales, device, imL, imR, dispL, maskL)
    print("Inspection execution time: %s" %
          (timeit.default_timer()-start_time))

    # visualize.imshow_3ch(imL.squeeze(0).cpu(), 'imL')
    # visualize.imshow_3ch(imR.squeeze(0).cpu(), 'imR')
    #
    # for i, im in enumerate(predictions_dict.values()):
    #     time.sleep(1)
    #     visualize.imshow_1ch(im['after'][0].cpu(), str(i), [0, dispL.max()])
    # visualize.imshow_1ch(dispL[0].cpu(), 'dispL')
    # image_pcg = evaluate.image_percentage_over_limit(predictions_dict[0]['after'].cpu(),
    #                                                  dispL.cpu(), maskL.cpu(), 3)
    # visualize.imshow_1ch(image_pcg[0], 'over_thres')


if __name__ == '__main__':
    # import config file
    conf_path = './../../conf.ini'
    conf = configparser.ConfigParser()
    conf.read(conf_path)

    # add parent path, if not already added
    parent_path = conf['PATHS']['parent_dir']
    sys.path.insert(1, parent_path) if parent_path not in sys.path else 0

    # run main
    run(conf)
