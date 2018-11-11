import gimp


def copy_layer(image_src, layer_name_src, image_dst, layer_name_dst, position_dst=0):
    """
    :type image_src: gimp.Image
    :type layer_name_src: str
    :type image_dst: gimp.Image
    :type layer_name_dst: str
    :type position_dst: int
    """
    layer_src = gimp.pdb.gimp_image_get_layer_by_name(image_src, layer_name_src)
    layer_dst = gimp.pdb.gimp_image_get_layer_by_name(image_dst, layer_name_dst)
    if layer_dst is None:
        layer_dst = gimp.pdb.gimp_layer_new(
            image_dst,
            layer_src.width,
            layer_src.height,
            layer_src.type,
            layer_name_dst,
            layer_src.opacity,
            layer_src.mode
        )
        gimp.pdb.gimp_image_add_layer(image_dst, layer_dst, 0)

    gimp.pdb.gimp_edit_copy(layer_src)
    layer_floating = gimp.pdb.gimp_edit_paste(layer_dst, True)
    gimp.pdb.gimp_floating_sel_anchor(layer_floating)
    reorder_layer(image_dst, layer_dst, position_dst)


def reorder_layer(image, layer, position):
    """
    :type image: gimp.Image
    :type layer: gimp.Layer
    :type position: int
    """
    gimp.pdb.gimp_image_reorder_item(image, layer, None, position)
