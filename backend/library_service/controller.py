import shutil
import cv2
import json
import os
import gridfs
import math
import sys
from flask import Response, request
from flask_restful import Resource
from pymongo import MongoClient
from bson import ObjectId
from mongoengine.errors import FieldDoesNotExist, NotUniqueError, DoesNotExist, \
    ValidationError, InvalidQueryError

sys.path.append(os.path.realpath(
    os.path.join(os.path.abspath(__file__), os.path.pardir, os.path.pardir, os.path.pardir)))

from backend.library_service.domain_model import Dataset, Page, Sample, Model
from backend.library_service.errors import SchemaValidationError, ModelAlreadyExistsError, \
    InternalServerError, UpdatingModelError, DeletingModelError, ModelNotExistsError


# class to handle GET and POST requests on all the known datasets collection
class DatasetsController(Resource):

    # get the collection of all datasets
    def get(self):
        try:
            # todo: create a DatasetService (or something along those lines)
            datasets = Dataset.objects.to_json()    # DatasetService.getAllDatasets()
            return Response(datasets, mimetype="application/json", status=200)
        except DoesNotExist:
            raise ModelNotExistsError
        except Exception:
            raise InternalServerError

    # add a new dataset to the collection
    def post(self):
        try:
            # get pages and samples from the request
            samples = request.form.get('annotations')
            samples_json = json.loads(samples)

            body = request.form.to_dict()
            body.pop('annotations')
            ds = Dataset(**body)
            ds.save()
            id = ds.id

            files = request.files.to_dict().items()
            for k, v in files:

                ds_img = Page()
                ds_img['filename'] = k
                ds_img['is_confirmed'] = samples_json[k]['is_confirmed']
                ds_img['list_active_texts'] = samples_json[k]['list_active_texts']
                ds_img['list_active_texts'] = [str(active_text_field) for active_text_field in ds_img['list_active_texts']]
                ds_img['index'] = samples_json[k]['index']
                ds_img.image.put(v.stream.read(), content_type='image/png')
                ds.pages.append(ds_img)

                if k in samples_json.keys():  # check if annotation is partial in current dataset
                    ann2add = samples_json[k]['boxes']
                    for elem in ann2add:
                        ann = Sample()
                        ann['x'] = elem['x']
                        ann['y'] = elem['y']
                        ann['width'] = elem['width']
                        ann['height'] = elem['height']
                        ann['text'] = elem['text']
                        ds_img.samples.append(ann)

            ds.save()

            return {'id': str(id)}, 200
        except (FieldDoesNotExist, ValidationError):
            raise SchemaValidationError
        except NotUniqueError:
            raise ModelAlreadyExistsError
        except Exception as e:
            raise InternalServerError


# class to handle GET, PUT, DELETE requests for a single dataset
class DatasetController(Resource):

    def get(self, id):
        try:
            ds = Dataset.objects.get(id=id).to_json()
            return Response(ds, mimetype='application/json', status=200)
        except DoesNotExist:
            raise DeletingModelError
        except Exception:
            raise InternalServerError

    # update a stored model
    def put(self, id):
        try:
            dataset = Dataset.objects.get(id=id)
            samples = request.form.get('annotations')
            samples_json = json.loads(samples)
            for i, k in enumerate(samples_json.keys()):
                ann2add = samples_json[k]['boxes']
                new_array = []
                for elem in ann2add:
                    ann = Sample()
                    ann['x'] = elem['x']
                    ann['y'] = elem['y']
                    ann['width'] = elem['width']
                    ann['height'] = elem['height']
                    ann['text'] = elem['text']
                    new_array.append(ann)

                dataset.pages[i].samples = new_array

            dataset.save()
            return 'updated model ' + str(id), 200
        except InvalidQueryError:
            raise SchemaValidationError
        except DoesNotExist:
            raise UpdatingModelError
        except Exception:
            raise InternalServerError

    # delete a stored model
    def delete(self, id):

        try:
            ds = Dataset.objects.get(id=id)
            ds.delete()
            return 'deleted dataset ' + str(id), 200
        except DoesNotExist:
            raise DeletingModelError
        except Exception:
            raise InternalServerError


class DatasetImageApi(Resource):

    def get(self, id_ds, id_img):
        try:
            ds = Dataset.objects.get(id=id_ds).to_json()
            db = MongoClient().HTR
            fs = gridfs.GridFS(db, collection='fs')
            filefile = fs.get(file_id=ObjectId(id_img)).read()
            return Response({filefile}, mimetype='image/png', status=200)

        except DoesNotExist:
            raise DeletingModelError
        except Exception:
            raise InternalServerError


def resize_image(img, short_size):
    height, width, _ = img.shape
    if height < width:
        new_height = short_size
        new_width = new_height / height * width
    else:
        new_width = short_size
        new_height = new_width / width * height
    new_height = int(round(new_height / 32) * 32)
    new_width = int(round(new_width / 32) * 32)
    resized_img = cv2.resize(img, (new_width, new_height))
    return resized_img, new_width, new_height


def resize_image_bigsize(img2resize, big_size):
    height, width, _ = img2resize.shape
    if height > width:
        new_height = big_size
        new_width = new_height / height * width
    else:
        new_width = big_size
        new_height = new_width / width * height
    new_height = int(round(new_height / 32) * 32)
    new_width = int(round(new_width / 32) * 32)
    resized_img = cv2.resize(img2resize, (new_width, new_height))
    return resized_img, new_width, new_height


class DatasetCreator(Resource):

    def post(self):

        try:
            samples = request.form.get('annotations')
            samples_json = json.loads(samples)
            dataset_name = request.form.get('name')
            files = request.files.to_dict().items()

            if not os.path.isdir(dataset_name):
                print('create folder', dataset_name)
                os.mkdir(dataset_name)

            dbnet_dataset = dict()  # DBNET
            dbnet_dataset['data_root'] = 'raw_images'  # DBNET
            dbnet_dataset['data_list'] = []  # DBNET
            dbnet_dataset_root_path = os.path.join(dataset_name, dbnet_dataset['data_root'])  # DBNET

            if not os.path.isdir(os.path.join(dataset_name, dbnet_dataset['data_root'])):  # DBNET
                os.mkdir(dbnet_dataset_root_path)

            gt_name = 'dataset.json'

            for index_file, (k, v) in enumerate(files):
                # filename_gt = k.split('.')[0] + '.json'
                filename_img = k
                boxes = samples_json[k]['boxes']
                v.save(os.path.join(dataset_name, 'raw_images', filename_img))  # save  full img

                ocr_folder_path = os.path.join(dataset_name, 'clips', k)
                if not os.path.isdir(ocr_folder_path):
                    os.makedirs(ocr_folder_path)

                img = cv2.imread(os.path.join(dataset_name, 'raw_images', filename_img))
                height, width, _ = img.shape
                img_resized, resized_w, resized_h = resize_image_bigsize(img, big_size=2500)
                cv2.imwrite(os.path.join(dataset_name, 'raw_images', filename_img), img_resized,
                            [cv2.IMWRITE_JPEG_QUALITY, 100])
                aspect_ratio_w = resized_w / width
                aspect_ratio_h = resized_h / height

                dbnet_dataset_elem = dict()  # DBNET
                dbnet_dataset_elem['img_name'] = filename_img  # DBNET
                dbnet_dataset_elem['annotations'] = []  # DBNET

                for index_box, box in enumerate(boxes):
                    x1, y1, w, h = box['x'], box['y'], box['width'], box['height']
                    x2, y2 = x1 + w, y1
                    x3, y3 = x1 + w, y1 + h
                    x4, y4 = x1, y1 + h
                    polygon = [[x1 * aspect_ratio_w, y1 * aspect_ratio_h], [x2 * aspect_ratio_w, y2 * aspect_ratio_h],
                               [x3 * aspect_ratio_w, y3 * aspect_ratio_h], [x4 * aspect_ratio_w, y4 * aspect_ratio_h]]

                    dbnet_annotation = dict()  # DBNET
                    dbnet_annotation['illegibility'] = False
                    dbnet_annotation['language'] = "Latin"
                    dbnet_annotation['chars'] = [{
                        'polygon': [],
                        'char': "",
                        'illegibility': False,
                        'language': "Latin"
                    }]

                    dbnet_annotation['polygon'] = polygon
                    dbnet_annotation['text'] = box['text']

                    dbnet_dataset_elem['annotations'].append(dbnet_annotation)

                    x = math.ceil(box['x'])
                    y = math.ceil(box['y'])
                    w = math.ceil(box['width'])
                    h = math.ceil(box['height'])
                    text = box['text']

                    crop_img = img[y:y + h, x:x + w]
                    file_name = str(index_file) + '_' + str(index_box)

                    cv2.imwrite(ocr_folder_path + '/' + dataset_name + '_' + file_name + '.jpg', crop_img,
                                [cv2.IMWRITE_JPEG_QUALITY, 100])
                    with open(ocr_folder_path + '/' + dataset_name + '_' + file_name + '.jpg.txt', "w",
                              encoding='utf-8') as gt:  # need text encoding?
                        gt.write(text)

                dbnet_dataset['data_list'].append(dbnet_dataset_elem)  # DBNET

            with open(dataset_name + '/' + gt_name, 'w') as gt_json:
                json.dump(dbnet_dataset, gt_json)

            shutil.copyfile('scripts/generate_dbnet_dataset.py', dataset_name + '/generate_dbnet_dataset.py')
            shutil.copyfile('scripts/generate_ocr_dataset.py', dataset_name + '/generate_ocr_dataset.py')
            shutil.copyfile('scripts/split.json', dataset_name + '/split.json')

            return True, 200

        except Exception as e:
            raise InternalServerError


class SegmentationDatasetCreator(Resource):

    def post(self):

        try:

            samples = request.form.get('annotations')
            samples_json = json.loads(samples)
            # dataset_name = request.form.get('name')+'-segmentation'
            dataset_name = 'dataset-segmentation'
            files = request.files.to_dict().items()

            if not os.path.isdir(dataset_name):
                print('create folder', dataset_name)
                os.mkdir(dataset_name)

            dbnet_dataset = dict()  # DBNET
            dbnet_dataset['data_root'] = 'images'  # DBNET
            dbnet_dataset['data_list'] = []  # DBNET
            dbnet_dataset_root_path = os.path.join(dataset_name, dbnet_dataset['data_root'])  # DBNET

            if not os.path.isdir(os.path.join(dataset_name, dbnet_dataset['data_root'])):  # DBNET
                os.mkdir(dbnet_dataset_root_path)

            gt_name = 'dbnet_dataset.json'

            for index, (k, v) in enumerate(files):
                # filename_gt = k.split('.')[0] + '.json'
                filename_img = k

                boxes = samples_json[k]['lines']
                v.save(os.path.join(dataset_name, 'images', filename_img))  # save  full img

                img = cv2.imread(os.path.join(dataset_name, 'images', filename_img))
                height, width, _ = img.shape
                img, resized_w, resized_h = resize_image_bigsize(img, short_size=2500)
                cv2.imwrite(os.path.join(dataset_name, 'images', filename_img), img, [cv2.IMWRITE_JPEG_QUALITY, 100])
                aspect_ratio_w = width / resized_w
                aspect_ratio_h = height / resized_h

                dbnet_dataset_elem = dict()  # DBNET
                dbnet_dataset_elem['img_name'] = filename_img  # DBNET
                dbnet_dataset_elem['annotations'] = []  # DBNET

                for box in boxes:
                    x1, y1, w, h = box['x'], box['y'], box['width'], box['height']
                    x2, y2 = x1 + w, y1
                    x3, y3 = x1 + w, y1 + h
                    x4, y4 = x1, y1 + h
                    polygon = [[x1 * aspect_ratio_w, y1 * aspect_ratio_h], [x2 * aspect_ratio_w, y2 * aspect_ratio_h],
                               [x3 * aspect_ratio_w, y3 * aspect_ratio_h], [x4 * aspect_ratio_w, y4 * aspect_ratio_h]]

                    dbnet_annotation = dict()  # DBNET
                    dbnet_annotation['illegibility'] = False
                    dbnet_annotation['language'] = "Latin"
                    dbnet_annotation['chars'] = [{
                        'polygon': [],
                        'char': "",
                        'illegibility': False,
                        'language': "Latin"
                    }]

                    dbnet_annotation['polygon'] = polygon
                    dbnet_annotation['text'] = box['text']

                    dbnet_dataset_elem['annotations'].append(dbnet_annotation)

                dbnet_dataset['data_list'].append(dbnet_dataset_elem)  # DBNET

            with open(dataset_name + '/' + gt_name, 'w') as gt_json:
                json.dump(dbnet_dataset, gt_json)

            shutil.copyfile('scripts/generate_dbnet_dataset.py', dataset_name + '/generate_dbnet_dataset.py')
            shutil.copyfile('scripts/split.json', dataset_name + '/split.json')

            return True, 200

        except Exception as e:
            raise InternalServerError


# class to handle  get and post operations on model collection
class ModelsApi(Resource):

    # get the collection of models
    def get(self):
        try:
            models = Model.objects.to_json()
            return Response(models, mimetype="application/json", status=200)
        except DoesNotExist:
            raise ModelNotExistsError
        except Exception:
            raise InternalServerError

    # add a new model to model collection
    def post(self):
        try:
            body = request.get_json()
            model = Model(**body)
            model.save()
            id = model.id
            return {'id': str(id)}, 200
        except (FieldDoesNotExist, ValidationError):
            raise SchemaValidationError
        except NotUniqueError:
            raise ModelAlreadyExistsError
        except Exception as e:
            raise InternalServerError


# class to handle get,put,delete operations on model
class ModelApi(Resource):

    def get(self, id):
        try:
            model = Model.objects.get(id=id).to_json()
            return Response(model, mimetype='application/json', status=200)
        except DoesNotExist:
            raise DeletingModelError
        except Exception:
            raise InternalServerError

    # update a stored model
    def put(self, id):
        try:
            body = request.get_json()
            Model.objects.get(id=id).update(**body)
            return 'updated model ' + str(id), 200
        except InvalidQueryError:
            raise SchemaValidationError
        except DoesNotExist:
            raise UpdatingModelError
        except Exception:
            raise InternalServerError

            # delete a stored model

    def delete(self, id):
        try:
            model = Model.objects.get(id=id)
            model.delete()
            return 'deleted model ' + str(id), 200
        except DoesNotExist:
            raise DeletingModelError
        except Exception:
            raise InternalServerError