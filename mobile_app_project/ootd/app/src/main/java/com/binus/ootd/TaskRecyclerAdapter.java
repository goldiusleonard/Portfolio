package com.binus.ootd;

import android.view.LayoutInflater;
import android.view.View;
import android.view.ViewGroup;
import android.widget.CheckBox;
import android.widget.ImageView;
import android.widget.TextView;

import androidx.annotation.NonNull;
import androidx.recyclerview.widget.RecyclerView;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.Date;

public class TaskRecyclerAdapter extends RecyclerView.Adapter<TaskRecyclerAdapter.MyViewHolder> {
    private ArrayList<Task> taskList;
    public TaskRecyclerAdapter(ArrayList<Task> taskList) {
        this.taskList = taskList;
    }

    @NonNull
    @Override
    public MyViewHolder onCreateViewHolder(@NonNull ViewGroup parent, int viewType) {
        View itemView = LayoutInflater.from(parent.getContext()).inflate(R.layout.task_view, parent, false);
        return new MyViewHolder(itemView);
    }

    @Override
    public void onBindViewHolder(@NonNull MyViewHolder holder, int position) {
        String taskTitle = taskList.get(position).getTitle();
//        String taskDeadline = taskList.get(position).getDeadline();

        holder.taskTitleText.setText(taskTitle);
        holder.taskDeadlineText.setText("Today");
    }

    @Override
    public int getItemCount() {
        return taskList.size();
    }

    public class MyViewHolder extends RecyclerView.ViewHolder {
        private TextView taskTitleText;
        private TextView taskDeadlineText;


        public MyViewHolder (final View view) {
            super(view);
            this.taskTitleText = view.findViewById(R.id.task_title);
            this.taskDeadlineText = view.findViewById(R.id.task_deadline);

        }

    }

}
