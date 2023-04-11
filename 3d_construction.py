import os
import tkinter as tk
from tkinter import filedialog, messagebox
import vtk
from pathlib import Path

class CTReconstructor:
    def __init__(self):
        self.filename = None
        self.image = None
        self.renderer = None

        # 创建Tkinter界面
        self.root = tk.Tk()
        self.root.title("CT 3D重构")

        # 创建文件选择框和文件名显示框
        file_frame = tk.Frame(self.root)
        file_frame.pack(fill=tk.X, padx=10, pady=10)
        file_label = tk.Label(file_frame, text="选择文件夹：")
        file_label.pack(side=tk.LEFT)
        self.filename_entry = tk.Entry(file_frame, width=50)
        self.filename_entry.pack(side=tk.LEFT, padx=10)
        file_button = tk.Button(file_frame, text="浏览", command=self.choose_dir)
        file_button.pack(side=tk.LEFT)

        # 创建重构按钮
        reconstruct_button = tk.Button(self.root, text="重构", command=self.reconstruct)
        reconstruct_button.pack(side=tk.TOP, padx=10, pady=10)

    def choose_dir(self):
        # 使用文件选择对话框获取文件夹名
        self.filename = filedialog.askdirectory()
        if self.filename:
            # 使用Path类处理路径
            self.filename = Path(self.filename)
            self.filename_entry.delete(0, tk.END)
            self.filename_entry.insert(0, self.filename)

    def reconstruct(self):
        self.filename = self.filename_entry.get()
        if not self.filename:
            # 如果没有选择文件夹，提示用户选择文件夹
            messagebox.showerror("错误", "请选择文件夹！")
            return

        
        # 创建vtkDICOMImageReader对象
        reader = vtk.vtkDICOMImageReader()
        path = Path(self.filename)
        str_path = str(path)
        directory_name = str_path.encode('gbk')
        reader.SetDirectoryName(directory_name)
        reader.Update()

        # 获取DICOM数据的范围
        min_value = reader.GetOutput().GetScalarRange()[0]
        max_value = reader.GetOutput().GetScalarRange()[1]

        # 创建vtkImageShiftScale对象来标准化数据
        shift_scale = vtk.vtkImageShiftScale()
        shift_scale.SetInputConnection(reader.GetOutputPort())
        shift_scale.SetOutputScalarTypeToUnsignedChar()
        shift_scale.SetShift(-min_value * 255 / (max_value - min_value))
        shift_scale.SetScale(255 / (max_value - min_value))
        shift_scale.Update()

        # 创建vtkSmartVolumeMapper和vtkVolume对象
        mapper = vtk.vtkSmartVolumeMapper()
        mapper.SetInputData(shift_scale.GetOutput())

        volume = vtk.vtkVolume()
        volume.SetMapper(mapper)

        # 创建vtkColorTransferFunction、vtkPiecewiseFunction对象
        color_tf = vtk.vtkColorTransferFunction()
        color_tf.AddRGBPoint(0, 0.0, 0.0, 0.0)
        color_tf.AddRGBPoint(30, 1.0, 0.0, 0.0)
        color_tf.AddRGBPoint(255, 1.0, 1.0, 0.0)

        opacity_tf = vtk.vtkPiecewiseFunction()
        opacity_tf.AddPoint(0, 0.0)
        opacity_tf.AddPoint(100, 0.0)
        opacity_tf.AddPoint(150, 0.5)
        opacity_tf.AddPoint(255, 1.0)

        # 设置vtkVolume的属性
        volume_property = vtk.vtkVolumeProperty()
        volume_property.SetColor(color_tf)
        volume_property.SetScalarOpacity(opacity_tf)
        volume_property.ShadeOn()

        volume.SetProperty(volume_property)

        # 创建vtkRenderer、vtkRenderWindow和vtkRenderWindowInteractor对象
        renderer = vtk.vtkRenderer()
        renderer.AddVolume(volume)

        window = vtk.vtkRenderWindow()
        window.AddRenderer(renderer)

        interactor = vtk.vtkRenderWindowInteractor()
        interactor.SetRenderWindow(window)

        # 第一个：添加vtkSliderWidget和vtkSliderRepresentation2D对象
        slider_rep = vtk.vtkSliderRepresentation2D()
        slider_rep.SetMinimumValue(0)
        slider_rep.SetMaximumValue(1)
        slider_rep.SetValue(opacity_tf.GetValue(50))
        slider_rep.SetTitleText("Opacity1")

        # 设置vtkSliderRepresentation2D的位置和大小
        slider_rep.GetPoint1Coordinate().SetCoordinateSystemToNormalizedViewport()
        slider_rep.GetPoint1Coordinate().SetValue(0.2, 0.05)
        slider_rep.GetPoint2Coordinate().SetCoordinateSystemToNormalizedViewport()
        slider_rep.GetPoint2Coordinate().SetValue(0.8, 0.05)
        slider_rep.SetSliderLength(0.05)
        slider_rep.SetSliderWidth(0.03)
        slider_rep.SetTubeWidth(0.005)

        slider_widget = vtk.vtkSliderWidget()
        slider_widget.SetInteractor(interactor)
        slider_widget.SetRepresentation(slider_rep)
        slider_widget.SetAnimationModeToAnimate()
        slider_widget.EnabledOn()


        # 定义vtkTextActor对象来添加文本标签
        text_actor = vtk.vtkTextActor()
        text_actor.SetInput("Use slider to adjust opacity")
        text_actor.GetTextProperty().SetFontFamilyToArial()
        text_actor.GetTextProperty().SetFontSize(18)
        text_actor.GetTextProperty().SetColor(1.0, 1.0, 1.0)
        text_actor.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
        text_actor.GetPositionCoordinate().SetValue(0.02, 0.95)

        # 添加vtkTextActor对象到vtkRenderer中
        renderer.AddActor2D(text_actor)

        # 定义函数来更新透明度函数
        def update_opacity(obj, event):
            value1 = slider_rep.GetValue()

            opacity_tf.RemoveAllPoints()
            opacity_tf.AddPoint(0, 0.0)
            opacity_tf.AddPoint(100, value1)
            opacity_tf.AddPoint(200, 0.5)
            opacity_tf.AddPoint(255, 1)
            window.Render()

        slider_widget.AddObserver("InteractionEvent", update_opacity)

        # 在vtkRenderWindow中显示DICOM数据
        window.Render()
        interactor.Start()

    def run(self):
        # 运行Tkinter界面
        self.root.mainloop()

if __name__ == "__main__":
    app = CTReconstructor()
    app.run()