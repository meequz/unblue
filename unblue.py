#!/usr/bin/env python
# -*- coding: utf-8 -*-

from gimpfu import *


def set_parent_position(image, item, parent, position):
  name = pdb.gimp_item_get_name(item)
  position_item = pdb.gimp_image_get_item_position(image, item)
  if position > position_item:
    position += 1
  newlayer = pdb.gimp_layer_copy(item, FALSE)
  pdb.gimp_image_insert_layer(image, newlayer, parent, position)
  pdb.gimp_image_remove_layer(image, item)
  pdb.gimp_item_set_name(newlayer, name)
  return newlayer

def get_layer_properties(layer):
  image = pdb.gimp_item_get_image(layer)
  name = pdb.gimp_item_get_name(layer)
  parent = pdb.gimp_item_get_parent(layer)
  position = pdb.gimp_image_get_item_position(image, layer)
  return image, name, parent, position

def duplicate_layer(layer):
  image, name, parent, position = get_layer_properties(layer)
  copy = pdb.gimp_layer_copy(layer, FALSE)
  pdb.gimp_image_insert_layer(image, copy, None, 0)
  copy = set_parent_position(image, copy, parent, position)
  return copy

def get_layer_by_number(image, number):
  num_layers, layer_ids = pdb.gimp_image_get_layers(image)
  return gimp.Item.from_id( layer_ids[number] )
  


def meequz_unblue(image, drawable, threshlevel, feath, denoise, blur, color_corr):
  pdb.gimp_context_push()
  #~ Забараняем запіс скасоўванняў
  pdb.gimp_image_undo_group_start(image)


  #~ запамінаем ўласцівасці арыгіналу
  original_layer = pdb.gimp_image_get_active_layer(image)
  original_name = pdb.gimp_item_get_name(original_layer)
  original_parent = pdb.gimp_item_get_parent(original_layer)
  original_position = pdb.gimp_image_get_item_position(image, original_layer)
  original_selection = pdb.gimp_selection_save(image)
  pdb.gimp_progress_update(0.04) # прагрэс

  #~ копія арыгінальнага пласта ўверх
  copy = pdb.gimp_layer_copy(original_layer, FALSE)
  pdb.gimp_image_insert_layer(image, copy, None, 0)
  pdb.gimp_progress_update(0.06) # прагрэс
  #~ копія 1 вылучанай вобласці ўверх
  pdb.gimp_edit_copy(image.active_drawable)
  copy1 = pdb.gimp_edit_paste(drawable, TRUE)
  pdb.gimp_floating_sel_to_layer(copy1)
  pdb.gimp_progress_update(0.08) # прагрэс

  #~ прыбраць вылучэнне
  pdb.gimp_selection_none(image)
  pdb.gimp_progress_update(0.1) # прагрэс
  
  #~ Разабралі
  image1, new_image1, new_image2, new_image3 = pdb.plug_in_decompose(image, copy1, "RGB", 4)
  red_layer = get_layer_by_number(image1, 0)
  green_layer = get_layer_by_number(image1, 1)
  pdb.gimp_progress_update(0.2) # прагрэс
  #~ Сабралі
  image2 = pdb.plug_in_drawable_compose(image1, red_layer, green_layer, green_layer, None, "RGB")
  pdb.gimp_progress_update(0.3) # прагрэс
  #~ выдаляем выяву 1
  pdb.gimp_image_delete(image1)
  pdb.gimp_progress_update(0.32) # прагрэс

  #~ пераключаемся на выяву 2
  im2_layer = pdb.gimp_image_get_active_layer(image2)
  pdb.gimp_progress_update(0.35) # прагрэс
  #~ дублюем ейны пласт
  im2_layer_dupl = duplicate_layer(im2_layer)
  pdb.gimp_progress_update(0.38) # прагрэс
  #~ парог
  pdb.gimp_threshold(im2_layer_dupl, threshlevel, 255)
  pdb.gimp_progress_update(0.41) # прагрэс
  #~ вылучэнне па колеру
  pdb.gimp_image_select_color(image2, 0, im2_layer_dupl, (0,0,0))
  pdb.gimp_progress_update(0.44) # прагрэс
  #~ змякчэнне вылучэння
  pdb.gimp_selection_feather(image2, feath)
  pdb.gimp_progress_update(0.47) # прагрэс
  #~ выдаляем пласт парога
  pdb.gimp_image_remove_layer(image2, im2_layer_dupl)
  pdb.gimp_progress_update(0.5) # прагрэс
  #~ CTRL+C
  pdb.gimp_edit_copy(image2.active_drawable)
  pdb.gimp_progress_update(0.53) # прагрэс
  #~ CTRL+V
  corr_layer = pdb.gimp_edit_paste(image.active_drawable, TRUE)
  pdb.gimp_floating_sel_to_layer(corr_layer)
  pdb.gimp_progress_update(0.56) # прагрэс

  #~ выдаляем выяву 2
  pdb.gimp_image_delete(image2)
  pdb.gimp_progress_update(0.59) # прагрэс
  #~ аб'яднаць уніз
  copy1 = pdb.gimp_image_merge_down(image, corr_layer, 0)
  pdb.gimp_progress_update(0.65) # прагрэс
  
  
  if denoise:
    #~ Разабралі
    image1, new_image1, new_image2, new_image3 = pdb.plug_in_decompose(image, copy1, "YCbCr_ITU_R470", 4)
    luma = get_layer_by_number(image1, 0)
    blueness = get_layer_by_number(image1, 1)
    redness = get_layer_by_number(image1, 2)
    pdb.gimp_progress_update(0.7) # прагрэс
    #~ Gaussian Blur
    pdb.plug_in_gauss(image1, blueness, blur, blur, 0)
    pdb.gimp_progress_update(0.75) # прагрэс
    pdb.plug_in_gauss(image1, redness, blur, blur, 0)
    pdb.gimp_progress_update(0.8) # прагрэс
    #~ Сабралі
    image2 = pdb.plug_in_drawable_compose(image1, luma, blueness, redness, None, "YCbCr_ITU_R470")
    pdb.gimp_progress_update(0.85) # прагрэс
    #~ выдаляем выяву 1
    pdb.gimp_image_delete(image1)
    pdb.gimp_progress_update(0.86) # прагрэс
    #~ CTRL+C
    pdb.gimp_edit_copy(image2.active_drawable)
    #~ CTRL+V
    denoise_l = pdb.gimp_edit_paste(image.active_drawable, TRUE)
    pdb.gimp_floating_sel_to_layer(denoise_l)
    pdb.gimp_progress_update(0.87) # прагрэс
    #~ выдаляем выяву 2
    pdb.gimp_image_delete(image2)
    pdb.gimp_progress_update(0.88) # прагрэс
    #~ колеракарэкцыя
    if color_corr:
      pdb.gimp_hue_saturation(denoise_l, 0, 0, 0, 16)
    #~ аб'яднаць уніз
    copy1 = pdb.gimp_image_merge_down(image, denoise_l, 0)
    pdb.gimp_progress_update(0.89) # прагрэс
    
  #~ аб'яднаць уніз
  copy = pdb.gimp_image_merge_down(image, copy1, 0)
  pdb.gimp_progress_update(0.9) # прагрэс
  
  #~ выдаленне арыгіналу
  pdb.gimp_image_remove_layer(image, original_layer)
  pdb.gimp_progress_update(0.92) # прагрэс
  # вынік пішам на месца арыгіналу з яго ўласцівасцямі
  pdb.gimp_item_set_name(copy, original_name)
  copy = set_parent_position(image, copy, original_parent, original_position)
  pdb.gimp_progress_update(0.94) # прагрэс


  #~ Узнаўляем вылучэнне
  pdb.gimp_image_select_item(image, 0, original_selection)
  pdb.gimp_progress_update(0.96) # прагрэс

  # Абнаўляем змесціва выявы
  pdb.gimp_displays_flush()
  pdb.gimp_progress_update(0.98) # прагрэс
  # Дазваляем запіс скасоўванняў
  pdb.gimp_image_undo_group_end(image)
  pdb.gimp_context_pop()


# Рэгіструем функцыю у PDB
register(
          "python-fu-meequz-unblue", # Назва функцыі, якая рэгіструецца
          "Removing blue stains from the shadow areas. It is not properly working with selection, only with layer. Sorry.", # Кароткае апісанне дзеянняў, якія выконваюцца
          "Removing blue stains from the shadow areas. 'Force' is what maximum of lightness considers as shadow. 'Feather' is how much bluring the boundaries. \"Denoise\" is boolean: yes or no. \"Blur\" is a radius of gaussian blur. Color-corr is boolean: yes or no.", # Звесткі пра плагін
          "Mihas Varantsou, (meequz@gmail.com)", # Звесткі пра аўтара
          "GPLv3", # Звесткі пра правы
          "March 2013", # Дата з'яўлення
          "Unblue shadow areas", # Назва ў меню
          "*", # Тыпы выяў, з якімі працуе плагін
          [
              (PF_IMAGE, "image", "Input image", None), # Указальнік на выяву
              (PF_DRAWABLE, "drawable", "Input drawable", None), # Указальнік на drawable
              (PF_SLIDER, "treshlevel", "Force", 67, (0, 255, 1)), # Ніжні парог
              (PF_SLIDER, "feath", "Feather", 5, (0, 64, 1)), # Змякчэнне краёў
              (PF_BOOL, "denoise", "YCbCr blur denoise", True), # Ці размыць шумы у прасторы YCbCr
              (PF_VALUE, "blur", "Blur radius for denoise", 42, (0, 1000, 1)), # Наколькі моцна размываць каляровыя шумы
              (PF_BOOL, "color_corr", "Color correction for denoise", True), # Ці карэктаваць колеры пасля шумаразмыцця
              
          ],
          [], # Спіс зменных, якія вяртае плагін
          meequz_unblue, menu="<Image>/Filters/Enhance/") # Назва крынінай функцыі і меню, дзе будзе змешчаны пункт запуску плагіна

# Запуск сцэнару
main()
